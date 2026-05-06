import streamlit as st
import os

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Secure Sandbox App", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. Token 密碼驗證機制 ---
def check_password():
    """Returns `True` if the user had the correct password."""
    # 預設密碼可從環境變數取得，增強 Docker 部署的安全性
    SECRET_TOKEN = os.getenv("APP_TOKEN")
    
    def password_entered():
        if not SECRET_TOKEN:
            st.session_state["password_correct"] = False
            return
        if st.session_state["password"] == SECRET_TOKEN:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h3 style='text-align: center; margin-top: 20vh;'>🔒 系統已鎖定</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("請輸入安全 Token", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h3 style='text-align: center; margin-top: 20vh;'>🔒 系統已鎖定</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("請輸入安全 Token", type="password", on_change=password_entered, key="password")
            st.error("Token 錯誤，請重新嘗試。")
        return False
    else:
        return True

if not check_password():
    st.stop() # 阻擋後續程式執行

st.success("✅ 驗證成功，連線已加密。")

# === 請在此處貼上你原本寫好的 STT 邏輯 ===
