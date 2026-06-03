# 1. ベースとなる軽量なPython環境を指定
FROM python:3.11-slim

# 2. コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 3. コンテナの動作に必要なシステムツール（SQLite等）をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 4. ローカルのファイルをすべてコンテナ内にコピー
COPY . .

# 5. 必要なPythonライブラリを一括インストール
# ※ requirements.txt があればそれを、なければ主要ライブラリをここで直接インストールします
RUN pip install --no-cache-dir streamlit openai

# 6. Streamlitが使用するポート番号（8080）を開放
EXPOSE 8080

# 7. 起動時のStreamlitの動作バグを防ぐ設定
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 8. アプリの起動コマンド
CMD ["streamlit", "run", "app.py"]

