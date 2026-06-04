import datetime
import os
import gspread
import google.auth
import openai
import streamlit as st

# ==========================================
# 1. 環境変数からOpenAIの鍵だけを取得
# ==========================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("環境変数が正しく設定されていません。Cloud Runの設定を確認してください。")
    st.stop()

# ==========================================
# 2. 各種外部サービスの初期化
# ==========================================
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@st.cache_resource
def init_spreadsheet():
    try:
        # JSONキーを使わず、Cloud Runの標準機能で安全に自動認証する
        credentials, project = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(credentials)
        
        # ご自身のスプレッドシート名
        sh = gc.open("quieresai_logs")
        return sh.worksheet("chat_logs")
    except Exception as e:
        st.error(f"スプレッドシートの接続に失敗しました: {e}")
        return None

worksheet = init_spreadsheet()

# ==========================================
# 3. データをスプレッドシートに保存する関数
# ==========================================
def save_chat_log(user_message, ai_message):
    if worksheet:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, user_message, ai_message])
        except Exception as e:
            print(f"ログ保存エラー: {e}")

# ==========================================
# 4. Streamlit UI 画面構築（Quieres AI）
# ==========================================
st.set_page_config(page_title="Quieres AI", page_icon="🤖", layout="centered")

# CSSでグラデーションのタイトルと丸いアイコン風デザインを追加
st.markdown("""
<style>
    .title-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .logo-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00E5FF, #8A2BE2);
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 24px;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(138, 43, 226, 0.3);
    }
    .gradient-text {
        font-size: 42px;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #00E5FF, #8A2BE2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
</style>

<div class="title-container">
    <div class="logo-circle">¿?</div>
    <h1 class="gradient-text">Quieres AI</h1>
</div>
""", unsafe_allow_html=True)

st.write("あなたに最適なAIツールを瞬時に提案するAIコンシェルジュです。")

# 🚨 ここが超重要！チャット履歴の箱を準備するコード
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去のチャット履歴を画面に再描画する
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 5. チャットの入力とAIの応答処理
# ==========================================
if user_input := st.chat_input("どのようなAIツールをお探しですか？"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはAIツールの専門コンシェルジュです。ユーザーの目的に合わせて最適なツールを提案してください。"},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                ],
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"AIの応答中にエラーが発生しました: {e}")
            full_response = "申し訳ありません。エラーが発生しました。"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_chat_log(user_input, full_response)
