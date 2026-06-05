FROM python:3.11-slim

WORKDIR /app

# faiss-cpuを本番のLinuxサーバーで組み立てるために必要な基礎部品を最初に仕込む
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 必要なシステムファイルをコピー
COPY requirements.txt .

# requirements.txt に書かれたすべての道具（langchain等）を本番サーバーに確実にインストール
RUN pip install --no-cache-dir -r requirements.txt

# 残りのプログラムファイルをコピー
COPY . .

# 🛡️ ポート番号をCloud Runの標準である 8080 に変更
EXPOSE 8080

# 🛡️ 起動コマンドのポートを 8080 に修正 ＆ 赤エラー画面を絶対に出さない設定
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--client.showErrorDetails=false", "--client.toolbarMode=minimal"]
