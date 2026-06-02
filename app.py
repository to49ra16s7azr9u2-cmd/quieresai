import streamlit as st
import sqlite3
import datetime
import os
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

# --- データベースの初期化（SQLite） ---
DB_FILE = "kieres_ai_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

init_db()

if "session_token" not in st.session_state:
    st.session_state["session_token"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
if "user_lang" not in st.session_state:
    st.session_state["user_lang"] = "jp"

# --- 35種類のAI グランドマスターデータベース ---
AI_MASTER_DATA = """
【論文検索・文献リサーチ】
1. Consensus (https://consensus.app/): 質問を投げると、何万もの学術論文から科学的根拠を抽出してYes/Noの割合まで可視化するAI検索。(無料枠あり)
2. scite (https://scite.ai/): 他の論文から「支持されているか」「批判されているか」の文脈をAIが自動分類する、信頼性検証の最高峰。(無料枠あり)
3. Elicit (https://elicit.org/): 膨大な論文から「データセット規模」や「実験方法」を自動抽出し、表形式で一括比較できる研究の神ツール。(無料枠あり)
4. SciSpace (https://typeset.io/): 論文PDFの数式や専門用語をハイライトするだけで、AIがその場で直感的に解説する解析ツール。(無料枠あり)
5. Google Scholar (https://scholar.google.com/): 世界最大の学術ネットワークから正確な被引用数と論文URLを瞬時にリサーチ。(無料)

【財務分析・データ解析】
1. Zerve (https://www.zerve.ai/): データサイエンス・統計分析に特化。コードの文脈やデータ構造を完全に維持したまま並列で開発・実験をアシストする環境。(無料枠あり)
2. Claude 3.5 Sonnet (https://claude.ai/): データやコードを元に、インタラクティブで見やすいグラフやダッシュボード（Artifacts機能）を即座に作る能力がダントツ。(無料枠あり)
3. ChatGPT Advanced Data Analysis (https://chatgpt.com/): エクセル、CSV、決算書を投げるだけで、pythonを裏で走らせてデータクリーニングから未来予測まで全自動化。(有料)
4. Julius AI (https://julius.ai/): 高度な統計処理（回帰分析、因果推論の検証など）や複雑なグラフ作成の精度が極めて高いデータサイエンス特化型。(無料枠あり)

【文章作成・プレゼン図解・超長文要約】
1. DeepSeek (https://www.deepseek.com/): 圧倒的な推論・文章解析能力を「完全無料」で提供する驚異の最先端オープンソースAI。(無料)
2. NotebookLM (https://notebooklm.google/): 手元のPDFやメモをアップロードすると、その情報だけに完全に基づいた「嘘をつかない自分専用の専門家AI」を作るリサーチ特化型。(無料)
3. Napkin AI (https://www.napkin.ai/): 文章を打ち込むだけで、その文脈にぴったりの「美しい図解やインフォグラフィック」を一瞬で自動生成する資料作成の神ツール。(無料枠あり)
4. Gamma (https://gamma.app/): 1行のテーマを伝えるだけで、プロレベルの美しいデザインのプレゼンスライドを構成から画像まで丸ごと自動生成。(無料枠あり)
5. Gemini 1.5 Pro (https://gemini.google.com/): 本10冊分（200万トークン）の超膨大な資料や、数時間の講義動画を丸ごと読み込ませて一瞬で要約・解析できる怪物AI。(無料枠あり)

【動画・画像・音声・音楽生成】
1. CapCut AI (https://www.capcut.com/): テキストを入れるだけで、自動で台本・音声・字幕付きの動画をハイクオリティに生成。(無料)
2. Runway Gen-3 (https://runwayml.com/): 映画クオリティの超リアルな映像をテキストから生成する最先端動画AI。(有料)
3. Midjourney (https://www.midjourney.com/): 芸術コンテストで賞が取れるレベルの最高峰グラフィック・絵を生成する画像AIの王者。(有料)
4. Suno AI (https://suno.com/): 作りたい曲のイメージを入力するだけで、プロレベルの歌声・伴奏付きの楽曲を2曲同時に爆速生成する音楽AIの頂点。(無料枠あり)
5. ElevenLabs (https://elevenlabs.io/): 人間と区別がつかないレベルのリアルな感情表現・声色の変化が可能な世界トップの音声合成AI。(無料枠あり)
6. HeyGen (https://www.heygen.com/): 自分の動画をアップロードするだけで、口の動き（リップシンク）まで完璧に合わせた多言語翻訳動画を作れるローカライズAI。(無料枠あり)

【コード作成・プログラミング】
1. Cursor (https://www.cursor.com/): プロジェクト全体の構造を理解し、指示だけでアプリを完成させる最強のAIエディタ。(無料枠あり)
2. Windsurf (https://codeium.com/windsurf): 最先端の次世代エージェントAIが、開発者に代わってバグを自律的に探して修正する超新星エディタ。(無料枠あり)
3. v0 (https://v0.dev/): 「こんな見た目のダッシュボードやサイトが欲しい」と言うだけで、綺麗なUIデザインコードを一瞬で生成。(無料)
4. Spline AI (https://spline.design/): テキストによる指示だけで、Webサイトに埋め込める立体的な3Dオブジェクトやアニメーションを自動生成。(無料枠あり)

【自動化・ワークフロー・翻訳】
1. Zapier Central (https://zapier.com/central): 何千もの外部アプリとAIを連携させ、独自の自律型自動化ワークフローをチャットで構築できるシステム。(無料枠あり)
2. DeepL (https://www.deepl.com/): 文脈を正確に読み取り、業界用語やニュアンスを完全に再現する世界最高峰の超高精度翻訳AI。(無料)

【AI作成・カスタマイズ】
1. Dify (https://dify.ai/): ノーコードで自分専用の高度なAIアプリや、独自のデータベース（RAG）を組み込んだチャットボットを爆速で作れる最強ツール。(無料)
2. Coze (https://www.coze.com/): LINE、Discord、WEBサイトと連携できるAIボットを視覚的なフローで簡単に作成可能。(無料)
3. GPTs (OpenAI) (https://chatgpt.com/): チャットで指示を出すだけで、特定の業務やプロンプトに特化した独自のChatGPTを作れる機能。(有料)

【リサーチ・情報検索】
1. Perplexity (https://www.perplexity.ai/): ネット上の最新情報をリアルタイムで調べて、信頼できる根拠URL付きで構造化された回答を出す検索の主役。(無料枠あり)
2. Felo (https://felo.ai/): 海外の英語・スペイン語サイトの情報も自動でリサーチし、日本語で完璧に構造化してまとめてくれるクロスリンガル検索。(無料)
3. Genspark (https://www.genspark.ai/): 調べたいテーマについて複数のサイトを並列リサーチし、自分専用のまとめページを自動作成。(無料)
"""

def save_chat_log(user_input, ai_response, lang):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (timestamp, session_id, user_input, ai_response, detected_lang) VALUES (?, ?, ?, ?, ?)",
        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state["session_token"], user_input, ai_response, lang)
    )
    conn.commit()
    conn.close()

# --- タイトル表示 ---
st.markdown("<div class='main-title'>¿Quieres AI?</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>何がしたいか入力してね！世界中のあらゆるAIから最適なツールを即答します。</div>", unsafe_allow_html=True)
st.divider()

# --- チャット履歴の表示 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! 今日はどんな作業やリサーチをしますか？\n\n（例：『数式のある論文を解説してほしい』『プロレベルの曲を作りたい』『英語の動画を自分の声でスペイン語にしたい』など、世界中のAIから提案します！）"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ユーザーからの入力処理 ---
if user_input := st.chat_input("ここにメッセージを入力..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 動的な言語判定
    text_lower = user_input.lower()
    if any(w in text_lower for w in ["hola", "video", "codigo", "buscar"]):
        st.session_state["user_lang"] = "es"
    elif any(w in text_lower for w in ["hello", "hi", "code", "search"]):
        st.session_state["user_lang"] = "en"
    else:
        st.session_state["user_lang"] = "jp"
        
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            response = "⚠️ OpenAI API Keyが設定されていません。StreamlitのSecretsに設定してください。"
            message_placeholder.markdown(response)
        else:
            try:
                client = OpenAI(api_key=api_key)
                
                system_prompt = f"""
                You are 'Kieres AI', a brilliant AI tools concierge with an absolute worldwide directory of AI tools.
                You have an absolute database of AI tools:
                {AI_DATABASE = AI_MASTER_DATA}
                
                Instructions:
                1. Respond completely in the user's language (Japanese, English, or Spanish).
                2. Intelligently map the user's request to the correct tools. If they ask about voice, music, audio, automation, or 3D, recommend the newly added world-class tools (e.g., ElevenLabs, Suno AI, HeyGen, Zapier Central, Spline AI).
                3. Always format tool names as clickable Markdown links using the exact URLs provided (e.g., [Suno AI](https://suno.com/)).
                4. Present the selected options beautifully with structured lists.
                5. Keep the response clean, fast, professional, and friendly.
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
                
                save_chat_log(user_input, response, st.session_state["user_lang"])
                
            except Exception as e:
                response = f"エラーが発生しました: {str(e)}"
                message_placeholder.markdown(response)
                
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- 管理者用サイドバー ---
with st.sidebar:
    st.title("📊 ログ・アナリティクス")
    if st.button("🔄 最新の会話ログを読み込む"):
        if os.path.exists(DB_FILE):
            import pandas as pd
            conn = sqlite3.connect(DB_FILE)
            df_chats = pd.read_sql_query("SELECT * FROM chat_logs ORDER BY id DESC", conn)
            st.write("📝 直近のデータ（上から新しい順）", df_chats.head(10))
            conn.close()