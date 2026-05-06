import os
import tempfile
import importlib

import streamlit as st

import main as core

core = importlib.reload(core)
FuzzyMatcher = core.FuzzyMatcher
GlossaryProcessor = core.GlossaryProcessor
LLMCorrector = core.LLMCorrector
SRTBuilder = core.SRTBuilder
correct_file_by_type = core.correct_file_by_type


# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Sonic Architecture",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- 1.5 密碼驗證機制 ---
def check_password():
    def password_entered():
        # 安全規範：絕對不可以在原始碼中留下明文 Fallback。
        # 強制依賴環境變數，若環境變數未注入，則出於安全考量直接封鎖系統。
        SECRET_TOKEN = os.getenv("APP_TOKEN")

        if not SECRET_TOKEN:
            st.error("🚨 嚴重錯誤：系統環境變數未注入 APP_TOKEN，出於安全考量，已封鎖所有登入請求。")
            st.session_state["password_correct"] = False
            return

        if st.session_state["password"] == SECRET_TOKEN:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown(
            "<h3 style='text-align: center; margin-top: 20vh; font-family: Space Grotesk;'>⚠️ 系統已鎖定</h3>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.text_input("請輸入通行密碼", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown(
            "<h3 style='text-align: center; margin-top: 20vh; font-family: Space Grotesk;'>⚠️ 系統已鎖定</h3>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.text_input("請輸入通行密碼", type="password", on_change=password_entered, key="password")
            st.error("密碼錯誤，請重新嘗試。")
        return False
    else:
        return True


if not check_password():
    st.stop()


# --- 2. 注入自定義 CSS (Swiss Design x Brutalism) ---
st.markdown(
    """
<style>
    /* 引入 Google Fonts: 襯線體 Bodoni Moda 與 幾何無襯線體 Space Grotesk */
    @import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&family=Space+Grotesk:wght@300..700&display=swap');

    /* 隱藏 Streamlit 預設元素，打破常規框架 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 基礎重置與高對比配色 */
    .stApp {
        background-color: #F4F4F0; /* 粗糙紙張灰白 */
        color: #111111; /* 絕對純黑 */
        font-family: 'Space Grotesk', sans-serif;
    }

    /* typography: 巨大且極具張力的標題 */
    h1, h2, h3, .hero-title {
        font-family: 'Bodoni Moda', serif !important;
        font-weight: 800 !important;
        color: #111111;
        letter-spacing: -0.05em;
    }

    .hero-title {
        font-size: clamp(2.5rem, 5vw, 4rem);
        line-height: 0.9;
        margin-top: 2vh;
        margin-bottom: 1rem;
        text-transform: uppercase;
        border-bottom: 4px solid #111111;
        padding-bottom: 0.5rem;
    }

    .accent-text {
        color: #FF3300; /* 視覺衝擊紅 */
        font-style: italic;
    }

    .manifesto {
        font-size: 1.1rem;
        max-width: 80%;
        margin-bottom: 2rem;
        line-height: 1.4;
        font-weight: 500;
        border-left: 4px solid #FF3300;
        padding-left: 1rem;
    }

    /* 粗獷主義按鈕 (Brutalism Buttons) */
    .stButton>button {
        background-color: #111111;
        color: #F4F4F0;
        border: 2px solid #111111;
        border-radius: 0;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 700;
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        box-shadow: 6px 6px 0px #FF3300;
        transition: all 0.2s ease;
        width: 100%;
        margin-top: 1rem;
    }

    .stButton>button:hover {
        transform: translate(-4px, -4px);
        box-shadow: 12px 12px 0px #FF3300;
        color: #F4F4F0;
        background-color: #111111;
        border-color: #111111;
    }

    .stButton>button:active {
        transform: translate(8px, 8px);
        box-shadow: 0px 0px 0px #FF3300;
    }

    /* 輸入框與上傳區塊的銳利化 */
    .stFileUploader, .stTextArea>div>div>textarea, .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border: 3px solid #111111 !important;
        border-radius: 0 !important;
        background-color: #ffffff !important;
        color: #111111 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        box-shadow: 4px 4px 0px #111111;
        transition: box-shadow 0.2s ease;
    }

    .stFileUploader:hover, .stTextArea>div>div>textarea:focus, .stTextInput>div>div>input:focus {
        box-shadow: 6px 6px 0px #FF3300;
    }

    /* Streamlit 的標籤文字調整 */
    .st-emotion-cache-10trblm, label {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        color: #111111 !important;
        margin-bottom: 0.5rem;
    }

    /* 自定義捲軸 */
    ::-webkit-scrollbar {
        width: 12px;
    }
    ::-webkit-scrollbar-track {
        background: #F4F4F0;
        border-left: 2px solid #111111;
    }
    ::-webkit-scrollbar-thumb {
        background: #FF3300;
        border: 2px solid #111111;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- 3. 核心區塊佈局 (Asymmetric Layout) ---

# Hero Section
st.markdown('<div class="hero-title">校正<br><span class="accent-text">SRT.</span></div>', unsafe_allow_html=True)

st.markdown(
    """
<div class="manifesto">
    透過發音特徵精確重構時間軸。<br>
    我們濾除雜訊，將語音辨識的誤差與絕對分類進行對齊。沒有多餘的干擾，只有純粹的產出。
</div>
""",
    unsafe_allow_html=True,
)

# Grid System (不對稱的 7:5 比例)
col_left, empty_col, col_right = st.columns([7, 1, 5])

with col_left:
    st.markdown("### 01. 藍圖輸入", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("上傳 SRT/TXT 檔案", type=["srt", "txt"])

    st.markdown("### 02. 專有名詞定義", unsafe_allow_html=True)
    glossary_text = st.text_area("請輸入專有名詞 (一行一個)", value="汪喵星球\n大型語言模型", height=120)

with col_right:
    st.markdown("### 03. 引擎授權", unsafe_allow_html=True)

    engine_type = st.selectbox("推論引擎", ["OpenAI", "Google Gemini", "LM Studio (本地端)"])

    if engine_type == "OpenAI":
        api_key = st.text_input("API KEY", type="password", placeholder="sk-...")
        base_url = None
        model_name = "gpt-4o-mini"
    elif engine_type == "Google Gemini":
        api_key = st.text_input("GEMINI API KEY", type="password", placeholder="AIza...")
        # 利用 OpenAI 套件相容 Gemini API Endpoint
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        model_name = "gemini-2.5-flash"
    else:
        # LM Studio
        api_key = "lm-studio"
        base_url = st.text_input("API URL", value="http://10.61.102.210:1234/v1")
        model_name = "local-model"

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # 創造留白
    process_btn = st.button("啟動重構")


# --- 4. 執行邏輯 ---
if process_btn:
    if not uploaded_file:
        st.error("錯誤：缺少 SRT 藍圖。")
    elif not api_key:
        st.error("錯誤：缺少授權金鑰 (API Key)。")
    else:
        st.markdown("---")
        st.markdown("### 正在重構時間軸...")

        with st.spinner("對齊語音特徵與語意結構中..."):
            input_suffix = os.path.splitext(uploaded_file.name)[1].lower() or ".srt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as tmp_in:
                tmp_in.write(uploaded_file.getvalue())
                input_path = tmp_in.name

            output_path = None

            try:
                # 呼叫 main.py 中的核心邏輯
                glossary = [g.strip() for g in glossary_text.split("\n") if g.strip()]
                corrector = LLMCorrector(api_key=api_key, model=model_name, base_url=base_url)

                status_text = st.empty()
                progress_bar = st.progress(50)
                if input_suffix == ".txt":
                    status_text.text("準備完整 TXT/STT 文字並發送至 LLM 進行校正...")
                else:
                    status_text.text("準備完整 SRT 字幕並發送至 LLM 進行全局語意校正...")

                corrected_text, output_ext = correct_file_by_type(input_path, corrector, glossary, threshold=85)
                output_path = os.path.splitext(input_path)[0] + "_corrected" + output_ext

                progress_bar.progress(100)

                # 直接寫入檔案
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(corrected_text)

                status_text.text("重構完成。")

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="下載校正後的字幕",
                        data=f,
                        file_name=f"reconstructed_subtitle{output_ext}",
                        mime="text/plain",
                    )
            except Exception as e:
                st.error(f"系統錯誤: {e}")
            finally:
                os.remove(input_path)
                if output_path and os.path.exists(output_path):
                    os.remove(output_path)
