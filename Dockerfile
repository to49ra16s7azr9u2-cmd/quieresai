FROM python:3.11-slim

WORKDIR /app

# 必要なシステムファイルをコピー
COPY requirements.txt .

# 🛡️ 修正ポイント：requirements.txt に書かれたすべての道具（langchain等）を本番サーバーに確実にインストールさせる
RUN pip install --no-cache-dir -r requirements.txt

# 残りのプログラムファイルをコピー
COPY . .

EXPOSE 8081

# 🛡️ 画面保護システム：Streamlitのエラー詳細（赤いトレースバック箱）を画面に絶対出さない設定で起動する
CMD ["streamlit", "run", "app.py", "--server.port=8081", "--server.address=0.0.0.0", "--client.showErrorDetails=false", "--client.toolbarMode=minimal"]
