"""
Xリスト自動要約→Gmail送信システム v3 (twikit + Gemini + Web設定画面)

使い方:
1. 設定画面を開く.bat をダブルクリック → ブラウザで設定を入力
2. main.py を実行（手動 or タスクスケジューラ）
"""
import asyncio
import json
import smtplib
import sys
import io
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from twikit import Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_RUN_FILE = os.path.join(SCRIPT_DIR, ".last_run")
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

# Windows文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# --- 設定読み込み ---

def _load_settings():
    """settings.json から設定を読み込む"""
    if not os.path.exists(SETTINGS_FILE):
        print("❌ settings.json が見つかりません。")
        print("   「設定画面を開く.bat」で設定を行ってください。")
        sys.exit(1)
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

_settings = _load_settings()
LIST_URL = _settings["list_url"]
GEMINI_API_KEY = _settings["gemini_api_key"]
GMAIL_USER = _settings["gmail_user"]
GMAIL_APP_PASSWORD = _settings["gmail_app_password"]
LIST_ID = LIST_URL.split('/')[-1]
X_COOKIES = _settings.get("x_cookies", {})


async def fetch_x_list():
    """twikit経由でXリストからツイートを取得"""
    print(f"[1/3] Xリスト取得中... (List ID: {LIST_ID})")

    client = Client('ja-JP')
    client.set_cookies(X_COOKIES)

    tweets = await client.get_list_tweets(LIST_ID)
    count = len(tweets)
    print(f"  → {count}件のツイートを取得")

    formatted = []
    for tweet in tweets:
        user = tweet.user.screen_name
        text = tweet.text
        time_str = tweet.created_at
        formatted.append(f"【@{user}】({time_str})\n{text}")

    return "\n\n---\n\n".join(formatted)


def summarize_with_gemini(raw_text, max_retries=3):
    """Gemini APIでツイートを要約（リトライ付き）"""
    print("[2/3] Gemini APIで要約中...")
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""あなたはAI・テクノロジー業界の情報アナリストです。

以下はX(Twitter)のAI関連リストから取得した本日({today})の投稿です。

【タスク】
1. 重要なトピックを抽出してください
2. 以下のカテゴリで整理してください：
   - 🤖 AI新モデル・技術発表
   - 📊 業界動向・ニュース
   - 💡 活用事例・Tips
   - 🏢 企業動向・資金調達
   - 📌 その他注目情報
3. 各項目は簡潔に2-3行でまとめてください
4. 重複する話題は統合してください
5. 最後に「本日の注目ポイント」を1-2文で

---

{raw_text}"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            print("  → 要約完了")
            return response.text
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait = 30 * (attempt + 1)
                print(f"  ⏳ レート制限。{wait}秒待機してリトライ... ({attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise

    return None


def send_email(summary):
    """Gmailで要約を送信"""
    print("[3/3] メール送信中...")
    today = datetime.now().strftime("%Y/%m/%d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📰 Xリスト AI要約 ({today})"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    msg.attach(MIMEText(summary, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print(f"  → {GMAIL_USER} に送信完了！")


def already_sent_today():
    """今日すでに送信済みかチェック"""
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            return f.read().strip() == today
    return False


def mark_sent_today():
    """今日送信済みとマーク"""
    today = datetime.now().strftime("%Y-%m-%d")
    with open(LAST_RUN_FILE, "w") as f:
        f.write(today)


async def async_main():
    print("=" * 50)
    print(f"Xリスト自動要約システム v3 - {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("=" * 50)

    if already_sent_today():
        print("📬 本日はすでに送信済みです。スキップします。")
        return

    try:
        raw_text = await fetch_x_list()
        if not raw_text:
            print("ツイートが取得できませんでした。")
            return

        summary = summarize_with_gemini(raw_text)
        if not summary:
            print("要約の生成に失敗しました。")
            return

        send_email(summary)
        mark_sent_today()
        print()
        print("✅ すべて完了しました！")

    except Exception as e:
        print(f"❌ エラー発生: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
