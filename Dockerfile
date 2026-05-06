FROM python:3.10-slim

# 設定環境變數避免互動式安裝卡住
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 安裝 curl 與 Node.js (供 localtunnel 使用)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安裝 localtunnel
RUN npm install -g localtunnel

# 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有專案檔案到容器內
COPY . .

# 賦予啟動腳本執行權限
RUN chmod +x start.sh

# 暴露 8503 Port (僅在容器內部暴露，不到宿主機)
EXPOSE 8503

# 使用啟動腳本作為 Entrypoint
CMD ["./start.sh"]
