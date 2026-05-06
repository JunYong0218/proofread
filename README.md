# Sonic Architecture - SRT/TXT 語意校正工具

這是一個基於 Streamlit 開發的高效能字幕與逐字稿校對工具。它結合了 **拼音模糊比對 (Fuzzy Matching)** 與 **大型語言模型 (LLM)** 技術，專門修復語音辨識 (STT) 產生的同音異字、專有名詞錯誤。

## 🌟 核心功能

- **SRT 字幕校正**：自動標記疑似錯字並發送至 LLM 進行上下文語意修復，同時確保時間軸 (Timestamps) 100% 準確。
- **純文本 (TXT) 校正**：支援長篇逐字稿校對，修正錯別字並優化標點符號。
- **專有名詞字典**：可自定義專有名詞清單，透過拼音比對強制修正品牌名、產品名。
- **多引擎支援**：相容 OpenAI、Google Gemini 以及本地端 LM Studio。
- **密碼保護機制**：內建簡易的環境變數存取控制。

## 🚀 快速開始

### 本地開發模式

1. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**：
   建立 `.env` 檔案並加入：
   ```env
   APP_TOKEN=你的通行密碼
   ```

3. **啟動應用程式**：
   ```bash
   streamlit run streamlit_app.py
   ```

### Docker 部署模式

1. **使用 Docker Compose 啟動**：
   ```bash
   docker-compose up -d --build
   ```
   預設會啟動在 `8501` 端口。

## 🛠️ 技術棧

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Core Logic**: Python, [pysrt](https://pypi.org/project/pysrt/), [thefuzz](https://pypi.org/project/thefuzz/)
- **LLM Integration**: OpenAI SDK (Compatible with Gemini & LM Studio)
- **Deployment**: Docker, Docker Compose

## 📝 使用說明

1. 輸入「通行密碼」進入系統。
2. 上傳您的 `.srt` 或 `.txt` 檔案。
3. 在專有名詞欄位輸入需要精確修正的詞彙（一行一個）。
4. 選擇您的 LLM 引擎並輸入 API Key。
5. 點擊「啟動重構」，完成後即可下載校正後的檔案。

