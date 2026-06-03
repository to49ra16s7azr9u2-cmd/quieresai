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

# --- 🎨 限界突破：外資系ハイエンドSaaS風 グラスモルフィズムCSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. 全体のベース（背景・最高峰のフォントシステム） */
    .stApp {
        background: linear-gradient(135deg, #060814 0%, #0b0b1e 50%, #15112a 100%);
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* 2. 【最重要】もっさり感を消すため、メインコンテンツの横幅を拡張・最適化 */
    [data-testid="stMainBlockContainer"] {
        max-width: 900px !important;
        padding-top: 4rem !important;
        padding-bottom: 6rem !important;
    }
    
    /* 3. メインタイトル：圧倒的モダンなタイポグラフィ */
    .main-title {
        font-size: 3.6rem !important;
        font-weight: 800 !important;
        text-align: center;
        letter-spacing: -0.06em !important;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    
    /* 4. サブタイトル：繊細なホワイトウエイト */
    .sub-title {
        text-align: center;
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 1.1rem;
        font-weight: 400;
        letter-spacing: -0.02em;
        margin-bottom: 3.5rem;
    }
    
    /* 5. 入力エリア周囲の完全ステルス化（余白の無駄な浮きを排除） */
    [data-testid="stChatInputBottomBlankArea"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    footer, [data-testid="stFooterBlock"] {
        background: transparent !important;
        display: none !important;
    }
    
    /* 6. メッセージ入力コンテナ：極細の美ボーダーとスマートフォーカス */
    .stChatInputContainer {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: rgba(13, 18, 36, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        padding: 0.2rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .stChatInputContainer:focus-within {
        border-color: rgba(56, 189, 248, 0.5) !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.15), 0 10px 40px rgba(0, 0, 0, 0.4);
    }
    .stChatInputContainer textarea {
        color: #ffffff !important;
        font-size: 0.98rem !important;
    }
    .stChatInputContainer textarea::placeholder {
        color: rgba(255, 255, 255, 0.3) !important;
    }
    .stChatInputContainer button {
        color: #38bdf8 !important;
    }
    
    /* 7. 【劇的進化】チャットボックス：洗練された薄ガラスのコンテナデザイン */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    
    /* 8. テキスト表示の完全統一（パキッとしたホワイトと美しい行間） */
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] ol, 
    [data-testid="stChatMessage"] ul, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] strong {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 0.98rem !important;
        line-height: 1.75 !important;
        letter-spacing: -0.01em !important;
    }
    
    /* テック系特有の洗練されたスマートリンク（下線を消し、ホバーで滑らかに変色） */
    [data-testid="stChatMessage"] a {
        color: #38bdf8 !important;
        -webkit-text-fill-color: #38bdf8 !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        transition: all 0.2s ease;
    }
    [data-testid="stChatMessage"] a:hover {
        color: #c084fc !important;
        -webkit-text-fill-color: #c084fc !important;
        border-bottom-color: rgba(192, 132, 252, 0.6);
    }
    
    /* 9. アバターアイコンのスマート枠線化 */
    [data-testid="stChatMessageAvatar"] {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }
    
    /* ミニマルなローディングプログレスバー */
    div[data-testid="stProgress"] > div {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stProgress"] > div > div > div > div {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%) !important;
        height: 3px !important;
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
        margin: 2.5rem 0 !important;
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
    st.session_state.messages = [{"role": "assistant", "content": "今日はどんな作業をしますか？"}]

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
        
        # 🛠️ 固定タイマーを廃止し、AIの生成中（通信中）だけ的確に回り続けるローディングバー
        with st.spinner("AIコンシェルジュが思考中..."):
            
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
                    
                    # ここでOpenAIと通信している間、スピナー（バー）が的確に波打ち続けます
                    completion = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                    response = completion.choices[0].message.content
                    
                    # 生成が完了した瞬間に、自動でローディングが消えて回答が表示されます
                    message_placeholder.markdown(response)
                    save_chat_log(user_input, response, "jp")
                    
                except Exception as e:
                    response = f"エラーが発生しました: {str(e)}"
                    message_placeholder.markdown(response)
                
    st.session_state.messages.append({"role": "assistant", "content": response})