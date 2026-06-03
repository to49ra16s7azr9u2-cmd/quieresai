import datetime
import json
import os
import gspread
import openai
import streamlit as st

# ==========================================
# 1. 環境変数から安全に鍵（シークレット）を取得
# ==========================================
# OpenAI APIキーの取得
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# GoogleサービスアカウントJSONの取得と辞書型への変換
GOOGLE_CREDENTIALS_JSON_STR = os.environ.get("GOOGLE_CREDENTIALS_JSON")

# 認証情報がセットされているかチェック
if not OPENAI_API_KEY or not GOOGLE_CREDENTIALS_JSON_STR:
    st.error(
        "環境変数が正しく設定されていません。Cloud Runの設定を確認してください。"
    )
    st.stop()

# ==========================================
# 2. 各種外部サービスの初期化
# ==========================================
# OpenAIクライアントの初期化
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# Googleスプレッドシートの初期化（関数化してキャッシュ）
@st.cache_resource
def init_spreadsheet():
    try:
        # 文字列として入っているJSONをPythonの辞書に変換
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
        # 辞書データを使ってGoogleと通信開始
        gc = gspread.service_account_from_dict(creds_dict)
        # 「quieresai_logs」という名前のスプレッドシートを開く
        # ※実際のシート名に合わせて変更してください
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
            # [日時, ユーザーの発言, AIの返答] の順に行を追加
            worksheet.append_row([timestamp, user_message, ai_message])
        except Exception as e:
            print(f"ログ保存エラー: {e}")


# ==========================================
# 4. Streamlit UI 画面構築（Quieres AI）
# ==========================================
st.set_page_config(page_title="Quieres AI", page_icon="🤖", layout="centered")

st.title("💡 Quieres AI")
st.write("あなたに最適なAIツールを瞬時に提案するコンシェルジュです。")

# チャット履歴の保持（Streamlitのセッション状態）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去のチャット履歴を画面に再描画
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 5. チャットの入力とAIの応答処理
# ==========================================
if user_input := st.chat_input("どのようなAIツールをお探しですか？"):
    # ユーザーの発言を表示＆履歴に保存
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AIの応答を生成して表示
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # OpenAI APIの呼び出し (GPT-4o-miniを使用)
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはAIツールの専門コンシェルジュです。ユーザーの目的に合わせて最適なツールを提案してください。",
                    },
                    *[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                ],
                stream=True,
            )

            # 返答をリアルタイムに文字が流れるように表示（ストリーミング）
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"AIの応答中にエラーが発生しました: {e}")
            full_response = "申し訳ありません。エラーが発生しました。"

    # AIの返答を履歴に保存
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

    # 💾 裏側でこっそりGoogleスプレッドシートにログを自動保存
    save_chat_log(user_input, full_response)
