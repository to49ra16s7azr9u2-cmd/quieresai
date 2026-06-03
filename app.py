import streamlit st
import sqlite3
import datetime
import os
import json
import time
from openai import OpenAI

# --- ページ全体の基本設定 ---
st.set_page_config(
    page_title="キエレスAI (¿Quieres AI?)",
    page_icon="🧩",
    layout="centered"
)

# --- 🎨 視覚的完全統一：全文字ホワイト化カスタムCSS ---
st.markdown("""
<style>
    /* 1. 全体の背景と基本文字色の統一（最優先ホワイト） */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #ffffff !important;
    }
    
    /* 2. メインタイトルのグラデーション（ここだけロゴ装飾） */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* 3. サブタイトルのホワイト化 */
    .sub-title {
        text-align: center;
        color: #ffffff !important;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 4. 入力欄の周囲の白い背景・余白を完全にダーク化 */
    [data-testid="stChatInputBottomBlankArea"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    footer, [data-testid="stFooterBlock"] {
        background: transparent !important;
    }
    
    /* 5. メッセージ入力コンテナのホワイト＆ダークネオン化 */
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
        color: #ffffff !important; /* プレースホルダーの文字も白に統一 */
        opacity: 0.7;
    }
    
    /* 6. 送信ボタン（飛行機マーク）のカラー */
    .stChatInputContainer button {
        color: #38bdf8 !important;
    }
    
    /* 7. 【超重要】チャットボックス内部のあらゆるテキスト・マークダウンを漏れなく白にする */
    [data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 12px;
        border: 1px solid rgba(51, 65, 85, 0.8);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* AIの出力文、通常の段落、箇条書き、番号付きリスト、太字、リンクすべてを白に強制固定 */
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] ol, 
    [data-testid="stChatMessage"] ul, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] strong, 
    [data-testid="stChatMessage"] a {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* リンクの下線や装飾も白ベースに調整 */
    [data-testid="stChatMessage"] a {
        text-decoration: underline;
        font-weight: bold;
    }
    
    /* ローディングテキストのホワイト化 */
    div[data-testid="stProgress"] > div {
        color: #ffffff !important;
    }
    
    /* 8. 区切り線のカラー */
    hr {
        border-color: #334155 !important;
    }
    
    /* ローディングバーのネオンカスタム */
    div[data-testid="stProgress"] > div > div > div > div {
        background-color: #38bdf8 !important;
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

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! 今日はどんな作業やリサーチをしますか？"}]

for message in st.session_state.messages:
    avatar_icon = "🧩" if message["role"] == "assistant" else "✨"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

if user_input := st.chat_input("ここにメッセージを入力..."):
    with st.chat_message("user", avatar="✨"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="🧩"):
        message_placeholder = st.empty()
        
        progress_text = "AIコンシェルジュが思考中..."
        progress_bar = st.progress(40, text=progress_text)
        
        for percent_complete in range(40, 101, 5):
            time.sleep(0.05)
            progress_bar.progress(percent_complete, text=progress_text)
            
        progress_bar.empty()
        
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            response = "⚠️ OpenAI API Keyが設定されていません。"
            message_placeholder.markdown(response)
        else:
            try:
                client = OpenAI(api_key=api_key)
                system_prompt = f"You are 'Kieres AI', a brilliant AI tools concierge. You have a master database of AI tools in JSON format:\n{AI_MASTER_TEXT}\n\nInstructions:\n1. Respond completely in the user's language.\n2. Intelligently select and recommend tools with their detailed free/paid tiers and usage guides written in the database.\n3. CRITICAL: Format tool links as: [Tool Name](/?click_target_name=ToolName&click_target_url=OriginalURL)\n4. Present options beautifully with bullet points. Ensure the response text is extremely clean."
                
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