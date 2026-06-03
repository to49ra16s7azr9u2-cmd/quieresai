import streamlit as st
import sqlite3
import os
import pandas as pd

st.set_page_config(page_title="キエレスAI - 中央データ回収パネル", page_icon="📊", layout="wide")

st.title("📊 キエレスAI 中央データ回収・分析ダッシュボード")
st.caption("全利用者のリアルタイム会話ログおよび行動クリックログをここから一括回収・エクスポートできます。")
st.divider()

DB_FILE = "kieres_ai_logs.db"

if not os.path.exists(DB_FILE):
    st.warning("⚠️ まだデータベースファイルが生成されていないか、ログが存在しません。")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 1. 会話ログ（テキストマイニング用）")
        conn = sqlite3.connect(DB_FILE)
        df_chats = pd.read_sql_query("SELECT * FROM chat_logs ORDER BY id DESC", conn)
        conn.close()
        
        st.dataframe(df_chats, use_container_width=True)
        
        # RやSQL分析用にCSVで即時ダウンロードできるボタン
        csv_chats = df_chats.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 会話ログをCSVでダウンロード", data=csv_chats, file_name="kieres_chat_logs.csv", mime="text/csv")
        
    with col2:
        st.subheader("📈 2. 行動ログ（クリック・需要分析用）")
        conn = sqlite3.connect(DB_FILE)
        df_clicks = pd.read_sql_query("SELECT * FROM click_logs ORDER BY id DESC", conn)
        conn.close()
        
        st.dataframe(df_clicks, use_container_width=True)
        
        # クリック行動データのCSVダウンロードボタン
        csv_clicks = df_clicks.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 行動ログをCSVでダウンロード", data=csv_clicks, file_name="kieres_click_logs.csv", mime="text/csv")

    st.divider()
    st.subheader("💡 統計クイックサマリー")
    st.write(f"🧩 **総会話数**: {len(df_chats)} 回  |  🎯 **総外部リンククリック数**: {len(df_clicks)} 回")
