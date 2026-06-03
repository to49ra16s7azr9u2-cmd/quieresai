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

# --- 🎨 視覚的統一：Mi Quincena風・極限カスタムCSS ---
st.markdown("""
<style>
    /* 1. 全体の背景と基本文字色の統一 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #ffffff !important;
    }
    
    /* 2. メインタイトルのグラデーション */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* 3. サブタイトルの明瞭化 */
    .sub-title {
        text-align: center;
        color: #e2e8f0 !important;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 4. 【重要】入力欄の周囲の白い背景・余白を完全にダーク化 */
    [data-testid="stChatInputBottomBlankArea"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    footer, [data-testid="stFooterBlock"] {
        background: transparent !important;
    }
    
    /* 5. メッセージ入力コンテナ自体のダークネオン化 */
    .stChatInputContainer {
        border-radius: 15px !important;
        border: 1px solid #3b82f6 !important;
        background-color: #1e293b !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }
    .stChatInputContainer textarea {
        color: #ffffff !important;
    }
    .stChatInputContainer textarea::placeholder {
        color: #94a3b8 !important;
    }
    
    /* 6. 送信ボタン（飛行機マーク）のネオンホワイト化 */
    .stChatInputContainer button {
        color: #38bdf8 !important;
    }
    
    /* 7. チャットボックスの統一デザイン（境界線を滑らかに） */
    [data-testid="stChatMessage"] {
        color: #ffffff !important;
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 12px;
        border: 1px solid rgba(51, 65, 85, 0.8);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] a {
        color: #ffffff !important;
    }
    
    /* 8. 区切り線のカラー変更 */
    hr {
        border-color: #334155 !important;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "kieres_ai_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS chat_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, session_id TEXT, user_input TEXT, ai_response TEXT, detected_lang TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS click_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, session_id TEXT, ai_name TEXT, url TEXT)")
    conn.commit()
    conn.close()

init_db()

def load_ai_database():
    json_path = "ai_data.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

AI_LIST_DATA = load_ai_database()
AI_MASTER_TEXT = json.dumps(AI_LIST_DATA, ensure_ascii=False, indent=2)

if "session_token" not in st.session_state:
    st.session_state["session_token"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def save_chat_log(user_input, ai_response, lang):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (timestamp, session_id, user_input, ai_response, detected_lang) VALUES (?, ?, ?, ?, ?)", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["session_token"], user_input, ai_response, lang))
    conn.commit()
    conn.close()

def save_click_log(ai_name, url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO click_logs (timestamp, session_id, ai_name, url) VALUES (?, ?, ?, ?)", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["session_token"], ai_name, url))
    conn.commit()
    conn.close()

query_params = st.query_params
if "click_target_name" in query_params and "click_target_url" in query_params:
    target_name = query_params["click_target_name"]
    target_url = query_params["click_target_url"]
    save_click_log(target_name, target_url)
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{target_url}\'">', unsafe_allow_html=True)
    st.stop()

# --- タイトル表示 ---
st.markdown("<div class='main-title'>¿Quieres AI?</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>何がしたいか入力してね！世界中のあらゆるAIから最適なツールを即答します。</div>", unsafe_allow_html=True)
st.divider()

# --- 💬 会話履歴の保持 ＆ アイコンの完全統一（🧩 と ✨） ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "今日はどんな作業をしますか？"}]

for message in st.session_state.messages:
    # ロール（発言者）に応じてアイコンを動的に完全上書き
    avatar_icon = "🧩" if message["role"] == "assistant" else "✨"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

if user_input := st.chat_input("ここにメッセージを入力..."):
    # ユーザー発言（✨アイコン）
    with st.chat_message("user", avatar="✨"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # アシスタント発言（🧩アイコン）
    with st.chat_message("assistant", avatar="🧩"):
        message_placeholder = st.empty()
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            response = "⚠️ OpenAI API Keyが設定されていません。"
            message_placeholder.markdown(response)
        else:
            try:
                client = OpenAI(api_key=api_key)
                system_prompt = f"You are 'Kieres AI', a brilliant AI tools concierge. You have a master database of AI tools in JSON format:\n{AI_MASTER_TEXT}\n\nInstructions:\n1. Respond completely in the user's language.\n2. Intelligently select and recommend tools.\n3. CRITICAL: Format tool links as: [Tool Name](/?click_target_name=ToolName&click_target_url=OriginalURL)\n4. Present options beautifully with bullet points."
                
                api_messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages[-6:]:
                    api_messages.append({"role": "assistant" if m["role"] == "assistant" else "user", "content": m["content"]})
                
                completion = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                save_chat_log(user_input, response, "jp")
            except Exception as e:
                response = f"エラーが発生しました: {str(e)}"
                message_placeholder.markdown(response)
                
    st.session_state.messages.append({"role": "assistant", "content": response})