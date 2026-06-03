import streamlit as st
import sqlite3
import datetime
import os
import json
from openai import OpenAI

# --- ページ全体の基本設定 ---
st.set_page_config(
    page_title="キエレスAI (¿Quieres AI?)",
    page_icon="🧩",
    layout="centered"
)

# --- 🎨 Mi Quincena風 高級カスタムCSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stChatInputContainer {
        border-radius: 15px !important;
        border: 1px solid #3b82f6 !important;
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    hr {
        border-color: #334155 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- データベースの初期化（SQLite：会話ログ＋行動クリックログ） ---
DB_FILE = "kieres_ai_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 会話ログ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            session_id TEXT,
            user_input TEXT,
            ai_response TEXT,
            detected_lang TEXT
        )
    """)
    # 【新設】行動クリックログ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS click_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            session_id TEXT,
            ai_name TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 💾 【自動化】JSONデータファイルの読み込み関数 ---
def load_ai_database():
    json_path = "ai_data.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 起動時にデータベースのテキスト表現を生成
AI_LIST_DATA = load_ai_database()
AI_MASTER_TEXT = json.dumps(AI_LIST_DATA, ensure_ascii=False, indent=2)

if "session_token" not in st.session_state:
    st.session_state["session_token"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# --- ログ保存用関数 ---
def save_chat_log(user_input, ai_response, lang):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (timestamp, session_id, user_input, ai_response, detected_lang) VALUES (?, ?, ?, ?, ?)",
        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["session_token"], user_input, ai_response, lang)
    )
    conn.commit()
    conn.close()

def save_click_log(ai_name, url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO click_logs (timestamp, session_id, ai_name, url) VALUES (?, ?, ?, ?)",
        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["session_token"], ai_name, url)
    )
    conn.commit()
    conn.close()

# --- 🎯 【行動ログ】リンク中継システム ---
# URLパラメータにクリックイベントが含まれているかチェック
query_params = st.query_params
if "click_target_name" in query_params and "click_target_url" in query_params:
    target_name = query_params["click_target_name"]
    target_url = query_params["click_target_url"]
    
    # クリック行動を即座にスタック
    save_click_log(target_name, target_url)
    
    # JavaScriptで外部サイトへ爆速リダイレクト（一過性の逆利用インフラ）
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{target_url}\'">', unsafe_allow_html=True)
    st.write(f"🔗 {target_name} へジャンプしています...")
    st.stop()

# --- メイン画面表示 ---
st.markdown("<div class='main-title'>¿Quieres AI?</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>何がしたいか入力してね！世界中のあらゆるAIから最適なツールを即答します。</div>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! 今日はどんな作業やリサーチをしますか？"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("ここにメッセージを入力..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            response = "⚠️ OpenAI API Keyが設定されていません。"
            message_placeholder.markdown(response)
        else:
            try:
                client = OpenAI(api_key=api_key)
                
                # 【重要】プロンプト内で「クリック計測用の中継リンク」を作るようLLMに命令
                system_prompt = f"""
                You are 'Kieres AI', a brilliant AI tools concierge.
                You have a master database of AI tools in JSON format:
                {AI_MASTER_TEXT}
                
                Instructions:
                1. Respond completely in the user's language (Japanese, English, or Spanish).
                2. Intelligently select and recommend appropriate tools from the database to solve the user's problem.
                3. CRITICAL: When outputting a link to a tool, you MUST NOT link to the original URL directly. Instead, you MUST format it as a tracking link pointing back to this app with query parameters so we can log the user's behavior.
                   Use this exact format for links:
                   [Tool Name](/?click_target_name=ToolName&click_target_url=OriginalURL)
                   Example: If recommending Consensus, use: [Consensus](/?click_target_name=Consensus&click_target_url=https://consensus.app/)
                4. Present options beautifully with bullet points and clear, short explanations.
                """
                
                api_messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages[-6:]:
                    api_messages.append({"role": "assistant" if m["role"] == "assistant" else "user", "content": m["content"]})
                
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages
                )
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
                save_chat_log(user_input, response, "jp")
                
            except Exception as e:
                response = f"エラーが発生しました: {str(e)}"
                message_placeholder.markdown(response)
                
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- 管理者用サイドバー（ログ確認） ---
with st.sidebar:
    st.title("📊 ログ・アナリティクス")
    import pandas as pd
    
    if st.button("🔄 会話ログを読み込む"):
        if os.path.exists(DB_FILE):
            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query("SELECT * FROM chat_logs ORDER BY id DESC", conn)
            st.write(df.head(5))
            conn.close()
            
    if st.button("📈 【新機能】行動ログ（クリック数）を読み込む"):
        if os.path.exists(DB_FILE):
            conn = sqlite3.connect(DB_FILE)
            df_clicks = pd.read_sql_query("SELECT * FROM click_logs ORDER BY id DESC", conn)
            st.write(df_clicks.head(10))
            conn.close()