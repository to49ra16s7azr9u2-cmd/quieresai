import os
import pandas as pd
from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    # 🌟【重要】ここに直接キーを書き込みます（Windowsのブロックを完全に回避します）
    os.environ["OPENAI_API_KEY"] = "ここにAPIKEY"
    # 1. 保存したCSVファイルの名前を指定
    csv_file = "ai_models.csv"
    
    if not os.path.exists(csv_file):
        print(f"エラー: {csv_file} が見つかりません。同じフォルダに置いてください。")
        return

    print("🔄 CSVファイルからデータを読み込んでいます...")
    # CSVLoaderを使って、AIが読み込みやすい形式でデータをパースします
    loader = CSVLoader(file_path=csv_file, encoding="utf-8")
    documents = loader.load()

    print("🧠 OpenAIのAPIを使って、データを数値（ベクトル）に変換しています...")
    # 超低コストなEmbedding API（text-embedding-3-small）を使って文字を数値化します
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print("💾 軽量データベース（FAISS）を作成して保存しています...")
    # 数値化したデータを、ローカルに「faiss_index」というフォルダを作って保存します
    db = FAISS.from_documents(documents, embeddings)
    db.save_local("faiss_index")

    print("✨ 完了しました！フォルダ内に『faiss_index』が作成されました。")

if __name__ == "__main__":
    main()
