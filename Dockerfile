FROM python:3.11-slim

WORKDIR /app

# 🛡️ faiss-cpuを本番のLinuxサーバーで組み立てるために必要な基礎部品（C++コンパイラ等）を最初に仕込む
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 必要なシステムファイルをコピー
COPY requirements.txt .

# requirements.txt に書かれたすべての道具（langchain等）を本番サーバーに確実にインストール
RUN pip install --no-cache-dir -r requirements.txt

# 残りのプログラムファイルをコピー
COPY . .

EXPOSE 8081

# 🛡️ 画面保護システム：Streamlitのエラー詳細（赤いトレースバック箱）を画面に絶対出さない設定で起動する
CMD ["streamlit", "run", "app.py", "--server.port=8081", "--server.address=0.0.0.0", "--client.showErrorDetails=false", "--client.toolbarMode=minimal"]
