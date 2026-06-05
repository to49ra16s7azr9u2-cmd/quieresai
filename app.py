import datetime
import os
import sys
import gspread
import google.auth
import openai
import streamlit as st
# 🌟 RAG追加: データベースの読み込みに必要な道具をインポート
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# ====================================================================
# 🛡️ 画面保護システム: 予期せぬ赤エラー（トレースバック）の表示を強制シャットアウト
# ====================================================================
def hide_streamlit_traceback(exception_type, exception_value, traceback):
    # 赤い画面を出す代わりに、オシャレな警告メッセージだけをスマートに表示させる
    st.error("🤖 現在、コンシェルジュがシステムの定期メンテナンスを行っています。時間を置いて再度アクセスしてください。")

# Streamlitのエラーハンドラーをご自身のカスタムメッセージにすり替える
sys.excepthook = hide_streamlit_traceback
# ==========================================
# 1. 環境変数からOpenAIの鍵だけを取得
# ==========================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 💡 ローカルPCテスト用の救済措置（黒い画面でsetし忘れた場合でも動くように自動補正します）
if not OPENAI_API_KEY:
    # クラウド環境でなければ、ここに直接キーを入れてテストすることも可能です
    # OPENAI_API_KEY = "sk-..." 
    st.error("環境変数が正しく設定されていません。Cloud Run、またはローカル環境の設定を確認してください。")
    st.stop()

# ==========================================
# 2. 各種外部サービスの初期化
# ==========================================
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 🌟 RAG追加: ライブラリ側（LangChain）にも確実にキーを認識させる
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

@st.cache_resource
def init_spreadsheet():
    try:
        credentials, project = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(credentials)
        sh = gc.open("quieresai_logs")
        return sh.worksheet("chat_logs")
    except Exception as e:
        st.error(f"スプレッドシートの接続に失敗しました: {e}")
        return None

worksheet = init_spreadsheet()

# 🌟 RAG追加: データベース（カンペ箱）を1回だけ読み込む関数
@st.cache_resource
def load_vector_db():
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # 先ほど生成に成功した「faiss_index」フォルダを読み込みます
        return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f"データベースの読み込みに失敗しました: {e}")
        return None

# 変数名を一貫させるため修正（最初上部で定義されていた vector_db を安全にセット）
vector_db = load_vector_db()

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
# 💡 カタカナ併記に変更し、検索エンジンに強くしました！
st.set_page_config(page_title="Quieres AI (キエレスAI) - AIツールコンシェルジュ", page_icon="🤖", layout="centered")

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
    <h1 class="gradient-text">Quieres AI (キエレスAI)</h1>
</div>
""", unsafe_allow_html=True)

st.write("キエレスAIは、あなたに最適なAIツールを瞬時に提案するAIコンシェルジュです。")

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
            # 🌟 RAG修正: ユーザーの質問に最も近いカンペを3つ、裏で偵察してくる
            context = ""
            if vector_db:
                docs = vector_db.similarity_search(user_input, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])

            # 🧠 AIへの指示書（【最新のAIモデルデータ】として裏で取得した context を埋め込みました！）
            system_prompt = f"""
            あなたはAIツールの専門コンシェルジュ「Quieres AI（キエレスAI）」です。ユーザーの目的に合わせて最適なツールを提案してください。
            提案する際は、ユーザーが比較検討しやすいように、必ず以下のフォーマットに従って詳細に説明してください。

            以下の【最新のAIモデルデータ（独自知識）】は、一般のGPTがまだ詳しく知らない最新情報、あるいは特に正確に答えるべき重要なデータです。
            ユーザーの質問がこのデータに関連している場合は、こちらに記載されている有料プランの金額、無料プランの範囲、公式URL、公開時期などを最優先で参考にして案内してください。
            
            ただし、このデータに載っていない一般的な知識や、関連する応用アドバイス、ユーザーへの共感の言葉などは、あなた自身が持つ膨大な知識を自由に組み合わせて、親切で自然な会話として広げて回答してください。

            【最新のAIモデルデータ（独自知識）】
            {context}

            【提案フォーマット】
            ### 1. [ツール名](公式URL) と概要
            （※ツール名の部分は、必ずそのツールの実際の公式ウェブサイトへのリンクを含めたマークダウン形式 `[ツール名](URL)` で出力してください。その後、なぜそのツールが目的に合致しているのかを簡潔に説明してください。）

            ### 2. 他のツールと比較した独自の強み
            （競合ツールや類似サービスと比べて、特に何が優れているのか、どのような人に最も向いているのかを明確に差別化して説明）

            ### 3. 無料版と有料版の違い
            （無料版でできること、制限事項。および有料版の価格帯や解放される機能、メリットを詳細に比較）

            ### 4. 具体的な使い方・始め方
            （どのような手順で登録し、どう入力すれば期待する結果が得られるか、具体的なステップを説明）
            
            ※複数のツールを提案する場合は、それぞれのツールに対して上記のフォーマットを繰り返してください。

            【最後に：比較表の作成】
            すべてのツールの紹介が終わった後、回答の最後に必ず、提案した全ツールを一目で比較できる「マークダウン形式の比較表」を作成してください。
            表の項目は「ツール名」「主な強み」「無料版の有無」「有料版の目安料金」「こんな人におすすめ」とし、ユーザーが最適なものを選びやすいように整理してください。

            プロフェッショナルかつ、初心者に寄り添った分かりやすいトーンで回答してください。
            """

            # ⏳ ここにローディングアニメーションを追加！
            with st.spinner("AIが世界中のツールから最適なものを厳選・比較しています..."):
                
                # OpenAI APIの呼び出し
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    ],
                    stream=True,
                )

                # 返答をリアルタイムに表示
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")

            # （※withブロックの外に出ることで、ローディングが自動的に消えます）
            response_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"AIの応答中にエラーが発生しました: {e}")
            full_response = "申し訳ありません。エラーが発生しました。"

    # AIの返答を履歴に保存
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # スプレッドシートに保存
    save_chat_log(user_input, full_response)
