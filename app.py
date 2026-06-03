import streamlit as st
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

# --- 🎨 究極の洗練：外資系AIテック風 グラスモルフィズムCSS ---
st.markdown("""
<style>
    /* 1. グローバルフォント＆バックグラウンドのモダン化 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #110f24 100%);
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* 2. メインタイトル：極細かつ大胆なハイエンドグラデーション */
    .main-title {
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        text-align: center;
        letter-spacing: -0.05em !important;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    /* 3. サブタイトル：タイポグラフィの美しさを際立たせる */
    .sub-title {
        text-align: center;
        color: #ffffff !important;
        font-size: 1.05rem;
        font-weight: 400;
        letter-spacing: -0.01em;
        opacity: 0.8;
        margin-bottom: 2.5rem;
    }
    
    /* 4. 入力エリア周囲の完全ステルス化（余白のホワイトアウトを絶対防御） */
    [data-testid="stChatInputBottomBlankArea"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    footer, [data-testid="stFooterBlock"] {
        background: transparent !important;
    }
    
    /* 5. メッセージ入力コンテナ：枠線を細くし、シームレスに背景へ溶け込ませる */
    .stChatInputContainer {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        transition: border-color 0.3s ease;
    }
    .stChatInputContainer:focus-within {
        border-color: rgba(56, 189, 248, 0.8) !important;
    }
    .stChatInputContainer textarea {
        color: #ffffff !important;
        font-size: 0.95rem !important;
    }
    .stChatInputContainer textarea::placeholder {
        color: #ffffff !important;
        opacity: 0.4;
    }
    .stChatInputContainer button {
        color: #38bdf8 !important;
    }
    
    /* 6. チャットメッセージ：グラスモルフィズム（半透明ガラス）デザイン */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* 7. マークダウンテキストの完全ホワイトアウト＆行間最適化 */
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] ol, 
    [data-testid="stChatMessage"] ul, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] strong, 
    [data-testid="stChatMessage"] a {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 0.95rem !important;
        line-height: 1.65 !important;
        letter-spacing: -0.005em !important;
    }
    
    /* テック系特有の洗練されたハイパーリンク（下線を消し、ホバーで光らせる） */
    [data-testid="stChatMessage"] a {
        text-decoration: none !important;
        color: #38bdf8 !important;
        -webkit-text-fill-color: #38bdf8 !important;
        font-weight: 600 !important;
        border-bottom: 1px solid rgba(56, 189, 248, 0.3);
        transition: all 0.2s ease;
    }
    [data-testid="stChatMessage"] a:hover {
        color: #818cf8 !important;
        -webkit-text-fill-color: #818cf8 !important;
        border-bottom-color: #818cf8 !important;
    }
    
    /* 8. アバターアイコン（絵文字）のサイズと余白の微調整 */
    [data-testid="stChatMessageAvatar"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* ローディングテキスト＆バーのミニマル化 */
    div[data-testid="stProgress"] > div {
        color: #ffffff !important;
        font-size: 0.85rem !important;
        opacity: 0.7;
    }
    div[data-testid="stProgress"] > div > div > div > div {
        background-gradient: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%) !important;
        background-color: #38bdf8 !important;
        height: 4px !important;
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
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