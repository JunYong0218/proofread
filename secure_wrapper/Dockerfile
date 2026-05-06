FROM python:3.10-slim

# 設定環境變數避免套件安裝時產生互動視窗卡死
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 安裝 curl 與 Node.js (供 localtunnel 使用)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安裝 localtunnel
RUN npm install -g localtunnel

# 安裝必要的 Python 套件 (可自行加入原本的 pypinyin, pysrt 等)
RUN pip install --no-cache-dir streamlit

# 複製本地端程式碼與啟動腳本
COPY app.py .
COPY start.sh .

# 賦予腳本執行權限
RUN chmod +x start.sh

# 暴露 8503 Port (僅在容器內部網路流通，對應架構規則 2)
EXPOSE 8503

# 使用啟動腳本作為 Entrypoint
CMD ["./start.sh"]
