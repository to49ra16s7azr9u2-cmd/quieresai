import streamlit as st
import sqlite3
import os
import pandas as pd

# --- ページ全体の基本設定 ---
st.set_page_config(page_title="キエレスAI - 中央データ回収パネル", page_icon="🛡️", layout="wide")

# --- 🎨 管理画面用：スタイリッシュなダーク・セキュアCSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        color: #ffffff !important;
    }
    h1, h2, h3, p, label, span {
        color: #ffffff !important;
    }
    /* パスワード入力欄のカスタマイズ */
    .stTextInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
    }
    /* データフレームの視認性向上 */
    [data-testid="stDataFrame"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔐 管理者用パスワード設定（ここを好きな文字に変えてください） ---
ADMIN_PASSWORD = "admin123"

# --- セッション状態でログイン成否を管理 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 🚪 ログイン画面の表示 ---
if not st.session_state["logged_in"]:
    st.vertical_space = st.empty()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center; margin-top: 5rem;'>🔒 Administrator Login</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8 !important;'>キエレスAI 中央データ回収システム</p>", unsafe_allow_html=True)
        st.write("")
        
        # パスワード入力（Enterキー、またはボタンクリックで認証）
        input_password = st.text_input("マスターパスワードキーを入力してください", type="password", key="admin_password_input")
        login_button = st.button("ログイン 🔓", use_container_width=True)
        
        if login_button or (input_password and st.session_state.get("admin_password_input")):
            if input_password == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.rerun()  # 画面を再起動してダッシュボードを表示
            elif input_password != "":
                st.error("🔑 パスワードが正しくありません。アクセス権限が拒否されました。")
                
    st.stop() # ログインしていない場合は、これ以降のコード（データ読み込み）を絶対に実行しない

# --- 📊 ログイン成功後に表示されるダッシュボード内容 ---
st.title("📊 キエレスAI 中央データ回収・分析ダッシュボード")
st.caption("認証済み：マスターデータアクセス権限（全利用者の会話ログ・行動ログをリアルタイム回収中）")

# ログアウトボタンを右上に配置
col_title, col_logout = st.columns([6, 1])
with col_logout:
    if st.button("ログアウト 🚪", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

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
        
        csv_chats = df_chats.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 会話ログをCSVでダウンロード", data=csv_chats, file_name="kieres_chat_logs.csv", mime="text/csv")
        
    with col2:
        st.subheader("📈 2. 行動ログ（クリック・需要分析用）")
        conn = sqlite3.connect(DB_FILE)
        df_clicks = pd.read_sql_query("SELECT * FROM click_logs ORDER BY id DESC", conn)
        conn.close()
        
        st.dataframe(df_clicks, use_container_width=True)
        
        csv_clicks = df_clicks.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 行動ログをCSVでダウンロード", data=csv_clicks, file_name="kieres_click_logs.csv", mime="text/csv")

    st.divider()
    st.subheader("💡 統計クイックサマリー")
    st.markdown(f"<h3>🧩 <b>総会話数</b>: {len(df_chats)} 回  |  🎯 <b>総外部リンククリック数</b>: {len(df_clicks)} 回</h3>", unsafe_allow_html=True)