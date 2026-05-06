import os
from pathlib import Path

import pysrt
from openai import OpenAI
from pypinyin import Style, pinyin
from thefuzz import fuzz


class GlossaryProcessor:
    """
    1. 專有名詞處理模組 (Glossary Processor)
    負責讀取專有名詞列表，並將其轉換為無聲調的拼音字串，以供後續模糊比對使用。
    """

    def __init__(self, glossary: list[str]):
        self.glossary = glossary
        # 建立 名詞 -> 拼音 的對照表
        self.pinyin_map = self._build_pinyin_map()

    def _build_pinyin_map(self) -> dict[str, str]:
        pinyin_map = {}
        for word in self.glossary:
            # 轉換為無聲調拼音，例如: "汪喵星球" -> ["wang", "miao", "xing", "qiu"]
            py_list = pinyin(word, style=Style.NORMAL)
            # 展平並結合成字串: "wang miao xing qiu"
            py_str = " ".join([p[0] for p in py_list])
            pinyin_map[word] = py_str
        return pinyin_map


class FuzzyMatcher:
    """
    2. SRT 解析與拼音模糊比對模組 (Fuzzy Matcher)
    解析 SRT，將字幕轉換為拼音，並與專有名詞字典進行模糊比對，若拼音高度相似但在字面上不完全一致，則標註候選詞。
    """

    def __init__(self, glossary_processor: GlossaryProcessor, threshold: int = 85):
        self.glossary_processor = glossary_processor
        self.threshold = threshold

    def _text_to_pinyin(self, text: str) -> str:
        # 將整句文本轉換為無聲調拼音
        py_list = pinyin(text, style=Style.NORMAL)
        return " ".join([p[0] for p in py_list])

    def process_srt(self, input_srt_path: str) -> list[dict]:
        """
        讀取 SRT 檔案並進行拼音比對與標註
        回傳包含原始字幕物件、原始文本與標註後文本的列表
        """
        subs = pysrt.open(input_srt_path, encoding="utf-8")
        processed_subs = []

        for sub in subs:
            # 去除字幕中可能的換行符號，以便於比對
            original_text = sub.text.replace("\n", " ")
            sub_pinyin = self._text_to_pinyin(original_text)

            marked_text = original_text

            # 檢查每個專有名詞是否可能存在於這句字幕中
            for word, word_pinyin in self.glossary_processor.pinyin_map.items():
                # 如果字面上已經完全包含該專有名詞（辨識完全正確），就不需要標記
                if word in original_text:
                    continue

                # 使用 partial_ratio 來找尋子字串的拼音相似度
                # 這樣可以正確處理長句子中包含該專有名詞拼音的情況
                similarity = fuzz.partial_ratio(word_pinyin, sub_pinyin)

                if similarity >= self.threshold:
                    # 發現高度相似的拼音，加上候選標記讓 LLM 決策
                    # 標記方式："接下來介紹汪喵刑求 [候選替換：汪喵星球]"
                    marked_text += f" [候選替換：{word}]"

            processed_subs.append(
                {
                    "sub_obj": sub,
                    "original_text": original_text,
                    "marked_text": marked_text,
                }
            )

        return processed_subs


class LLMCorrector:
    """
    3. LLM 語意校正模組 (LLM Corrector)
    將帶有候選標記的文本發送給外部 LLM API (如 OpenAI) 進行最後的語意決策與錯字修正。
    避免 OOM 問題，全程不在本地進行推論。
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = None):
        # 透過指定 base_url，OpenAI 套件也能相容 Gemini 與 LM Studio 的 API
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model

        self.system_prompt = (
            "你是一位擁有十年經驗的專業廣告剪輯師與字幕校對專家。\n"
            "以下是一段經過初步處理的影片 SRT 字幕，請幫我進行最終校對。\n\n"
            "【核心任務與規則】\n"
            "抓出所有同音異字： 語音辨識常有發音相似的錯字（例如：「開鄉」應為「開箱」、「優匯」應為「優惠」），請根據上下文邏輯全面修正。\n"
            "保護專有名詞： 文本中若有標註 [候選替換：某詞] 的提示，請判斷語意後套用正確的專有名詞。已經正確的品牌字（如汪喵星球）絕對不可修改。\n"
            "保護格式： 絕對不可以修改時間碼 00:00:00,000 --> 00:00:00,000 與字幕的數字編號。\n"
            "直接輸出： 請直接回傳修正後的完整 SRT 內容，不要加上任何解釋或標記。"
        )

    def correct_text(self, marked_text: str) -> str:
        """
        發送單句文本至 LLM 進行修正
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{marked_text}"},
                ],
                temperature=0.3,  # 調高一點點溫度，給予彈性去修正同音異字
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API 呼叫失敗: {e}")
            # 若發生錯誤，清除標籤後回傳原句以確保系統不會崩潰
            return marked_text.split(" [候選替換：")[0].strip()


    def correct_plain_text(self, stt_text: str, glossary: list[str] | None = None) -> str:
        """
        Correct a plain TXT/STT transcript. No timestamps are expected or generated.
        """
        glossary_text = "\n".join(glossary or [])
        user_content = (
            "以下是完整 STT 逐字稿，沒有 SRT 時間戳。\n"
            "請根據上下文修正同音異字、錯別字、標點與專有名詞。\n"
            "不要新增時間戳，不要改寫成摘要，不要加解釋，只輸出修復後的完整文字。\n\n"
        )
        if glossary_text:
            user_content += f"專有名詞參考：\n{glossary_text}\n\n"
        user_content += f"STT 內容：\n{stt_text}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位繁體中文 STT 逐字稿校對助手。"
                            "請修正辨識錯誤並保留原文語氣與段落，不要輸出任何說明。"
                        ),
                    },
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API plain text correction failed: {e}")
            return stt_text.strip()


    def correct_plain_text(self, stt_text: str, glossary: list[str] | None = None) -> str:
        """
        Correct a plain TXT/STT transcript without summarizing or adding timestamps.
        This later definition intentionally overrides the older garbled TXT prompt above.
        """
        glossary_text = "\n".join(glossary or [])
        user_content = (
            "以下是完整 STT 逐字稿，沒有 SRT 時間戳。\n"
            "請做逐字稿校對，不是摘要任務。\n"
            "你必須保留原文的所有資訊、句子順序、段落順序與語氣。\n"
            "不可刪句、不可縮寫、不可濃縮、不可合併成重點整理、不可改寫成摘要。\n"
            "只修正明顯的 STT 辨識錯誤、同音異字、錯別字、標點與專有名詞。\n"
            "如果某一句沒有錯，原句保留。\n"
            "不要新增時間戳，不要加解釋，只輸出修復後的完整逐字稿。\n\n"
        )
        if glossary_text:
            user_content += f"專有名詞參考：\n{glossary_text}\n\n"
        user_content += f"STT 原文開始：\n{stt_text}\nSTT 原文結束。"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位繁體中文 STT 逐字稿校對助手。"
                            "你的任務是完整校對，不是摘要。"
                            "輸出長度應接近原文；除非刪除的是明顯重複或無意義口吃，否則不得讓內容變少。"
                        ),
                    },
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=32000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API plain text correction failed: {e}")
            return stt_text.strip()


class SRTBuilder:
    """
    4. SRT 重組與輸出模組 (SRT Builder)
    將 LLM 回傳的純淨文本，與原本的 pysrt 時間碼物件重新結合，確保時間軸與原檔 100% 一致。
    """

    def __init__(self):
        pass

    def build_and_save(self, processed_subs: list[dict], output_path: str):
        """
        建立新的 SRT 物件並輸出為檔案
        """
        new_srt = pysrt.SubRipFile()

        for item in processed_subs:
            sub = item["sub_obj"]
            # 若 LLM 沒有回傳結果，則 fallback 回原始文本
            corrected_text = item.get("corrected_text", item["original_text"])

            # 建立新的 SubRipItem，保持原時間碼 start/end 不變
            new_sub = pysrt.SubRipItem(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                text=corrected_text,
            )
            new_srt.append(new_sub)

        # 產出後綴為 _corrected.srt 的新檔案
        new_srt.save(output_path, encoding="utf-8")
        print(f"已成功儲存校正後的 SRT 至：{output_path}")


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```srt"):
        cleaned = cleaned[6:]
    elif cleaned.startswith("```txt"):
        cleaned = cleaned[6:]
    elif cleaned.startswith("```text"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def build_marked_srt_text(input_path: str, glossary: list[str], threshold: int = 85) -> str:
    processor = GlossaryProcessor(glossary)
    matcher = FuzzyMatcher(processor, threshold=threshold)
    subs = matcher.process_srt(input_path)

    full_srt_text = ""
    for item in subs:
        sub = item["sub_obj"]
        full_srt_text += f"{sub.index}\n{sub.start} --> {sub.end}\n{item['marked_text']}\n\n"
    return full_srt_text


def correct_srt_file(input_path: str, corrector: LLMCorrector, glossary: list[str], threshold: int = 85) -> str:
    """
    Keep the original SRT path: preserve indexes/timestamps, send complete marked SRT to the LLM.
    """
    full_srt_text = build_marked_srt_text(input_path, glossary, threshold=threshold)
    return strip_code_fences(corrector.correct_text(full_srt_text))


def correct_txt_file(input_path: str, corrector: LLMCorrector, glossary: list[str] | None = None) -> str:
    """
    TXT mode: send the whole STT transcript to the LLM without adding timestamps.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        stt_text = f.read()
    return strip_code_fences(corrector.correct_plain_text(stt_text, glossary=glossary))


def correct_file_by_type(input_path: str, corrector: LLMCorrector, glossary: list[str], threshold: int = 85) -> tuple[str, str]:
    """
    Return (corrected_text, output_extension). SRT keeps the old timestamped workflow; TXT is plain text.
    """
    suffix = Path(input_path).suffix.lower()
    if suffix == ".srt":
        return correct_srt_file(input_path, corrector, glossary, threshold=threshold), ".srt"
    if suffix == ".txt":
        return correct_txt_file(input_path, corrector, glossary), ".txt"
    raise ValueError(f"Unsupported file type: {suffix or '(no extension)'}")


def main():
    """
    主程式：串接四個模組進行測試
    """
    # 0. 準備測試資料
    test_srt_path = "test_input.srt"
    output_srt_path = "test_input_corrected.srt"

    # 建立一個測試用的 SRT 檔案
    with open(test_srt_path, "w", encoding="utf-8") as f:
        f.write("1\n00:00:01,000 --> 00:00:04,000\n接下來介紹汪喵刑求\n\n")
        f.write("2\n00:00:04,500 --> 00:00:07,000\n這是一個大型與言模型\n\n")
        f.write("3\n00:00:07,500 --> 00:00:09,000\n我們已經正確辨識了汪喵星球\n\n")

    # 定義專有名詞列表
    glossary = ["汪喵星球", "大型語言模型"]

    # 請在此填入您的 OpenAI API Key。若為空，測試程式將進入 Mock 模式。
    api_key = os.getenv("OPENAI_API_KEY", "your_api_key_here")

    print("--- 1. 初始化專有名詞處理模組 ---")
    glossary_processor = GlossaryProcessor(glossary)
    print(f"字典拼音對照表: {glossary_processor.pinyin_map}")

    print("\n--- 2. 解析 SRT 與拼音模糊比對 ---")
    matcher = FuzzyMatcher(glossary_processor, threshold=85)
    processed_subs = matcher.process_srt(test_srt_path)

    for sub in processed_subs:
        print(f"原字幕: {sub['original_text']} -> 標記後: {sub['marked_text']}")

    print("\n--- 3. LLM 語意校正模組 ---")
    corrector = LLMCorrector(api_key=api_key)

    for item in processed_subs:
        # 如果沒有設定真實的 API_KEY，為了讓測試能順利執行到底，使用 Mock 回應
        if api_key == "your_api_key_here":
            if "汪喵刑求" in item["marked_text"]:
                item["corrected_text"] = "接下來介紹汪喵星球"
            elif "與言模型" in item["marked_text"]:
                item["corrected_text"] = "這是一個大型語言模型"
            else:
                item["corrected_text"] = item["original_text"]
            print(f"[Mock 模式] 校正結果: {item['corrected_text']}")
        else:
            print(f"正在呼叫 LLM 校正: {item['marked_text']} ...")
            corrected = corrector.correct_text(item["marked_text"])
            item["corrected_text"] = corrected
            print(f"校正結果: {item['corrected_text']}")

    print("\n--- 4. SRT 重組與輸出模組 ---")
    builder = SRTBuilder()
    builder.build_and_save(processed_subs, output_srt_path)

    print("\n執行完成！可以檢查產生的 test_input_corrected.srt 檔案。")


if __name__ == "__main__":
    main()
