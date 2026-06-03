import streamlit as st
import datetime
import os
import json
import time
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# --- ページ全体の基本設定 ---
st.set_page_config(
    page_title="キエレスAI (¿Quieres AI?)",
    page_icon="https://pub-c5e31b5cdafb419a86a69d5d343ea9cc.r2.dev/kieres_favicon.svg",
    layout="centered"
)

# --- 🎨 究極の洗練：Gemini風垂直ストリームCSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #060814 0%, #0b0b1e 50%, #15112a 100%);
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    [data-testid="stMainBlockContainer"] {
        max-width: 900px !important;
        padding-top: 4rem !important;
        padding-bottom: 6rem !important;
    }
    
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
    
    .sub-title {
        text-align: center;
        color: #ffffff !important;
        font-size: 1.1rem;
        font-weight: 400;
        letter-spacing: 0.05em;
        opacity: 0.7;
        margin-bottom: 3.5rem;
    }
    
    [data-testid="stChatInputBottomBlankArea"] { background: transparent !important; }
    footer, [data-testid="stFooterBlock"] { display: none !important; }
    
    .stChatInputContainer {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: rgba(13, 18, 36, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        padding: 0.2rem !important;
    }
    .stChatInputContainer:focus-within { border-color: rgba(56, 189, 248, 0.5) !important; }
    .stChatInputContainer textarea, .stChatInputContainer textarea::placeholder { color: #ffffff !important; }
    .stChatInputContainer button { color: #38bdf8 !important; }
    
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] ol, [data-testid="stChatMessage"] ul, 
    [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] strong, div[data-testid="stChatMessage"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 0.98rem !important;
        line-height: 1.8 !important;
    }
    
    [data-testid="stChatMessage"] ul, [data-testid="stChatMessage"] ol {
        padding-left: 1.5rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    [data-testid="stChatMessage"] a {
        color: #38bdf8 !important;
        -webkit-text-fill-color: #38bdf8 !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    }
    
    [data-testid="stChatMessageAvatar"], div[data-testid="stChatMessage"] > div:first-child { display: none !important; }
    
    .gemini-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; }
    .avatar-ai { width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%); box-shadow: 0 0 12px rgba(168, 85, 247, 0.5); }
    .avatar-user { width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); box-shadow: 0 0 12px rgba(56, 189, 248, 0.5); }
    .brand-name { font-size: 0.9rem !important; font-weight: 600 !important; opacity: 0.9; }
    div[data-testid="stProgress"] > div { color: #ffffff !important; }
    div[data-testid="stProgress"] > div > div > div > div { background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%) !important; height: 3px !important; }
    hr { border-color: rgba(255, 255, 255, 0.06) !important; margin: 2.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 📊 Googleスプレッドシート（データベース）接続設定 ---
# GCPで取得したJSONキーの中身を、GCRの環境変数から取得します
google_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

chat_sheet = None
click_sheet = None

if google_creds_json:
    try:
        creds_dict = json.loads(google_creds_json)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # ⚠️ ここにメモしたスプレッドシートIDを貼り付けてください！
        SPREADSHEET_ID = "ここにスプレッドシートIDを貼り付ける"
        
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        chat_sheet = spreadsheet.worksheet("chat_logs")
        click_sheet = spreadsheet.worksheet("click_logs")
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")

def save_chat_log(user_input, ai_response, lang):
    if chat_sheet:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = st.session_state.get("session_token", "unknown")
        chat_sheet.append_row([timestamp, session_id, user_input, ai_response, lang])

def save_click_log(ai_name, url):
    if click_sheet:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = st.session_state.get("session_token", "unknown")
        click_sheet.append_row([timestamp, session_id, ai_name, url])

# --- AIデータベース読み込み ---
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

query_params = st.query_params
if "click_target_name" in query_params and "click_target_url" in query_params:
    target_name = query_params["click_target_name"]
    target_url = query_params["click_target_url"]
    save_click_log(target_name, target_url)
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{target_url}\'">', unsafe_allow_html=True)
    st.stop()

# --- UI描画 ---
st.markdown("<div class='main-title'>¿Quieres AI?</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>目的を、最速で現実に。世界中のAIから最適なツールを即答します。</div>", unsafe_allow_html=True)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! 今日はどんな作業やリサーチをしますか？"}]

for message in st.session_state.messages:
    is_ai = (message["role"] == "assistant")
    avatar_class = "avatar-ai" if is_ai else "avatar-user"
    display_name = "¿Quieres AI?" if is_ai else "You"
    
    with st.chat_message(message["role"]):
        st.markdown(f"<div class='gemini-header'><div class='{avatar_class}'></div><div class='brand-name'>{display_name}</div></div>", unsafe_allow_html=True)
        st.markdown(message["content"])

if user_input := st.chat_input("ここにメッセージを入力..."):
    with st.chat_message("user"):
        st.markdown("<div class='gemini-header'><div class='avatar-user'></div><div class='brand-name'>You</div></div>", unsafe_allow_html=True)
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("AIコンシェルジュが思考中..."):
            api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            
            if not api_key:
                message_placeholder.markdown("⚠️ OpenAI API Keyが設定されていません。")
            else:
                try:
                    client = OpenAI(api_key=api_key)
                    system_prompt = f"You are 'Kieres AI', a brilliant AI tools concierge. You have a master database of AI tools in JSON format:\n{AI_MASTER_TEXT}\n\nInstructions:\n1. Respond completely in the user's language.\n2. Intelligently select and recommend tools with their detailed free/paid tiers and usage guides written in the database.\n3. CRITICAL: Format tool links as: [Tool Name](/?click_target_name=ToolName&click_target_url=OriginalURL)\n4. Present options beautifully with bullet points. Ensure the response text is extremely clean."
                    
                    api_messages = [{"role": "system", "content": system_prompt}]
                    for m in st.session_state.messages[-6:]:
                        api_messages.append({"role": "assistant" if m["role"] == "assistant" else "user", "content": m["content"]})
                    
                    completion = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                    response = completion.choices[0].message.content
                    
                    st.markdown("<div class='gemini-header'><div class='avatar-ai'></div><div class='brand-name'>¿Quieres AI?</div></div>", unsafe_allow_html=True)
                    message_placeholder.markdown(response)
                    
                    # 🚀 ここでGoogleスプレッドシートに保存されます！
                    save_chat_log(user_input, response, "jp")
                    
                except Exception as e:
                    message_placeholder.markdown(f"エラーが発生しました: {str(e)}")
                
    st.session_state.messages.append({"role": "assistant", "content": response})