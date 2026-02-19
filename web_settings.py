"""
Xリスト自動要約システム - ローカル設定画面 (Flask)
http://localhost:5000 で設定画面を開く
"""
import json
import os
import asyncio
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

app = Flask(__name__)
app.secret_key = "x_summary_local_key"


def load_settings():
    defaults = {
        "list_url": "",
        "gemini_api_key": "",
        "gmail_user": "",
        "gmail_app_password": "",
        "schedule_time": "07:00",
        "x_cookies": {"auth_token": "", "ct0": "", "twid": ""}
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            defaults.update(data)
    return defaults


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- 共通CSS ---

COMMON_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Meiryo', sans-serif; background: #0f1419; color: #e7e9ea; min-height: 100vh; }
.container { max-width: 680px; margin: 0 auto; padding: 24px 16px; }
header { text-align: center; padding: 32px 0 24px; border-bottom: 1px solid #2f3336; margin-bottom: 24px; }
header h1 { font-size: 24px; font-weight: 700; color: #1d9bf0; }
header p { color: #71767b; font-size: 14px; margin-top: 8px; }
a { color: #1d9bf0; text-decoration: none; }
a:hover { text-decoration: underline; }
.section { background: #16181c; border: 1px solid #2f3336; border-radius: 16px; padding: 24px; margin-bottom: 16px; }
.section h2 { font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
"""

# --- 設定画面テンプレート ---

HTML_TEMPLATE = (
"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Xリスト自動要約 - 設定</title>
<style>
"""
+ COMMON_CSS +
"""
.field { margin-bottom: 16px; }
.field-header { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.field-header label { font-size: 14px; color: #71767b; }
.field input[type="text"], .field input[type="password"] {
    width: 100%; padding: 12px 16px; background: #202327; border: 1px solid #333639;
    border-radius: 8px; color: #e7e9ea; font-size: 15px;
    font-family: 'Consolas', 'Courier New', monospace; transition: border-color 0.2s;
}
.field input:focus { outline: none; border-color: #1d9bf0; }
.field .hint { font-size: 12px; color: #71767b; margin-top: 4px; }
.btn-row { display: flex; gap: 12px; margin-top: 24px; }
.btn { padding: 12px 24px; border: none; border-radius: 9999px; font-size: 15px; font-weight: 700; cursor: pointer; transition: background 0.2s; }
.btn-primary { background: #1d9bf0; color: #fff; flex: 1; }
.btn-primary:hover { background: #1a8cd8; }
.btn-secondary { background: transparent; color: #1d9bf0; border: 1px solid #1d9bf0; }
.btn-secondary:hover { background: rgba(29,155,240,0.1); }
.alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.alert-success { background: rgba(0,186,124,0.15); color: #00ba7c; border: 1px solid rgba(0,186,124,0.3); }
.alert-error { background: rgba(244,33,46,0.15); color: #f4212e; border: 1px solid rgba(244,33,46,0.3); }
.alert-info { background: rgba(29,155,240,0.15); color: #1d9bf0; border: 1px solid rgba(29,155,240,0.3); }
.status-bar { display: flex; gap: 16px; flex-wrap: wrap; }
.status-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #71767b; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-green { background: #00ba7c; } .dot-red { background: #f4212e; } .dot-yellow { background: #ffd400; }
.toggle-pw { cursor: pointer; color: #71767b; font-size: 12px; user-select: none; }
.toggle-pw:hover { color: #1d9bf0; }
#testResult { margin-top: 12px; padding: 12px; border-radius: 8px; font-size: 13px; font-family: monospace; white-space: pre-wrap; display: none; }
"""
)

# ツールチップCSS
HTML_TEMPLATE += """
.tip {
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; border-radius: 50%;
    background: #333639; color: #71767b; font-size: 11px; font-weight: 700;
    cursor: help; position: relative; user-select: none;
    transition: background 0.2s, color 0.2s;
}
.tip:hover { background: #1d9bf0; color: #fff; }
.tip .tip-box {
    display: none; position: absolute; bottom: calc(100% + 8px); left: 50%;
    transform: translateX(-50%); width: 290px; padding: 12px 14px;
    background: #1e2732; border: 1px solid #3d5466; border-radius: 10px;
    font-size: 13px; font-weight: 400; color: #e7e9ea; line-height: 1.6;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4); z-index: 100; text-align: left;
    pointer-events: none;
}
.tip .tip-box::after {
    content: ''; position: absolute; top: 100%; left: 50%;
    transform: translateX(-50%); border: 6px solid transparent;
    border-top-color: #3d5466;
}
.tip:hover .tip-box { display: block; }
.tip .tip-box b { color: #1d9bf0; }
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>📰 Xリスト自動要約システム</h1>
        <p>設定画面 — ブラウザから全ての設定を管理できます</p>
        <p style="margin-top:12px;"><a href="/help" target="_blank">📖 初心者向けセットアップガイド</a></p>
    </header>

    {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %}
    {% endwith %}

    <form method="POST" action="/save">
"""

# フォーム本体
HTML_TEMPLATE += """
        <!-- Xリスト -->
        <div class="section">
            <h2>📱 Xリスト</h2>
            <div class="field">
                <div class="field-header">
                    <label>リストURL</label>
                    <span class="tip">？<span class="tip-box"><b>Xリストのアドレス</b><br>要約したいXリストのページURLです。Xでリストを開き、ブラウザのアドレスバーからコピーします。<br>形式: https://x.com/i/lists/数字</span></span>
                </div>
                <input type="text" name="list_url" value="{{ s.list_url }}" placeholder="例: https://x.com/i/lists/1234567890123456789">
            </div>
        </div>

        <!-- X Cookie -->
        <div class="section">
            <h2>🍪 X認証Cookie</h2>
            <div class="alert alert-info">Chrome DevTools (F12) → Application → Cookies → x.com から取得（<a href="/help#cookies" target="_blank">詳しい手順</a>）</div>
            <div class="field">
                <div class="field-header">
                    <label>auth_token</label>
                    <span class="tip">？<span class="tip-box"><b>ログイン認証トークン</b><br>Xにログイン済みであることを証明するキーです。<br><br>【取得方法】<br>Chrome で x.com を開く → F12 → Application → Cookies → x.com → 「auth_token」の Value をコピー</span></span>
                </div>
                <input type="password" name="auth_token" value="{{ s.x_cookies.auth_token }}" id="auth_token" placeholder="例: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2">
                <span class="toggle-pw" onclick="togglePw('auth_token')">👁 表示/非表示</span>
            </div>
            <div class="field">
                <div class="field-header">
                    <label>ct0</label>
                    <span class="tip">？<span class="tip-box"><b>CSRFトークン</b><br>不正リクエスト防止用のセキュリティ文字列です。<br><br>【取得方法】<br>auth_token と同じ Cookie 一覧で「ct0」の Value をコピー。長い英数字です。</span></span>
                </div>
                <input type="password" name="ct0" value="{{ s.x_cookies.ct0 }}" id="ct0" placeholder="例: abcd1234efgh5678ijkl9012mnop3456...">
                <span class="toggle-pw" onclick="togglePw('ct0')">👁 表示/非表示</span>
            </div>
            <div class="field">
                <div class="field-header">
                    <label>twid</label>
                    <span class="tip">？<span class="tip-box"><b>ユーザーID</b><br>あなたのXアカウントの数値IDです。<br><br>【取得方法】<br>同じ Cookie 一覧で「twid」の Value をコピー。「u%3D」で始まります。</span></span>
                </div>
                <input type="text" name="twid" value="{{ s.x_cookies.twid }}" placeholder="例: u%3D1234567890123456789">
            </div>
        </div>
"""

HTML_TEMPLATE += """
        <!-- Gemini API -->
        <div class="section">
            <h2>🤖 Gemini API</h2>
            <div class="field">
                <div class="field-header">
                    <label>APIキー</label>
                    <span class="tip">？<span class="tip-box"><b>Gemini AI の API キー</b><br>Google の AI（Gemini）を使うための鍵です。無料で発行できます。<br><br>【取得方法】<br><a href="https://aistudio.google.com/apikey" target="_blank" style="pointer-events:auto;color:#1d9bf0;">Google AI Studio</a> → 「APIキーを作成」→ コピー。「AIza」で始まる文字列です。</span></span>
                </div>
                <input type="password" name="gemini_api_key" value="{{ s.gemini_api_key }}" id="gemini_key" placeholder="例: AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5">
                <span class="toggle-pw" onclick="togglePw('gemini_key')">👁 表示/非表示</span>
                <div class="hint"><a href="https://aistudio.google.com/apikey" target="_blank">Google AI Studio</a> で無料取得</div>
            </div>
        </div>

        <!-- Gmail -->
        <div class="section">
            <h2>📧 Gmail送信設定</h2>
            <div class="field">
                <div class="field-header">
                    <label>Gmailアドレス</label>
                    <span class="tip">？<span class="tip-box"><b>送信元＆宛先の Gmail</b><br>要約メールの送信・受信に使う Gmail アドレスです。自分宛てに送信されます。</span></span>
                </div>
                <input type="text" name="gmail_user" value="{{ s.gmail_user }}" placeholder="例: yourname@gmail.com">
            </div>
            <div class="field">
                <div class="field-header">
                    <label>アプリパスワード</label>
                    <span class="tip">？<span class="tip-box"><b>Gmail 用アプリパスワード</b><br>通常の Gmail パスワードとは別の、アプリ専用16文字のパスワードです。2段階認証が必要です。<br><br>【取得方法】<br><a href="https://myaccount.google.com/apppasswords" target="_blank" style="pointer-events:auto;color:#1d9bf0;">Google アプリパスワード</a> → アプリ名を入力 → 作成 → 16文字をコピー（スペース除く）</span></span>
                </div>
                <input type="password" name="gmail_app_password" value="{{ s.gmail_app_password }}" id="gmail_pw" placeholder="例: abcdefghijklmnop">
                <span class="toggle-pw" onclick="togglePw('gmail_pw')">👁 表示/非表示</span>
                <div class="hint"><a href="https://myaccount.google.com/apppasswords" target="_blank">Googleアプリパスワード</a> で発行</div>
            </div>
        </div>

        <!-- 自動実行 -->
        <div class="section">
            <h2>⏰ 自動実行スケジュール</h2>
            <div class="field">
                <div class="field-header">
                    <label>毎日の実行時刻</label>
                    <span class="tip">？<span class="tip-box"><b>毎日の自動送信時刻</b><br>設定を保存すると、Windowsタスクスケジューラに自動登録されます。バックグラウンドで実行されるため、画面には何も表示されません。<br><br>変更したい場合は時刻を変えて再度「設定を保存」してください。</span></span>
                </div>
                <input type="time" name="schedule_time" value="{{ s.schedule_time }}" style="width: 160px; padding: 12px 16px; background: #202327; border: 1px solid #333639; border-radius: 8px; color: #e7e9ea; font-size: 15px;">
                <div class="hint">保存時にWindowsタスクスケジューラへ自動登録されます（バックグラウンド実行）</div>
            </div>
        </div>

        <div class="btn-row">
            <button type="submit" class="btn btn-primary">💾 設定を保存</button>
            <button type="button" class="btn btn-secondary" onclick="runTest()">🧪 テスト実行</button>
        </div>
    </form>

    <div id="testResult"></div>
"""

# ステータス＆JS
HTML_TEMPLATE += """
    <div class="section" style="margin-top: 24px;">
        <h2>📊 ステータス</h2>
        <div class="status-bar">
            <div class="status-item"><span class="dot {{ 'dot-green' if s.x_cookies.auth_token else 'dot-red' }}"></span> X Cookie: {{ '設定済み' if s.x_cookies.auth_token else '未設定' }}</div>
            <div class="status-item"><span class="dot {{ 'dot-green' if s.gemini_api_key else 'dot-red' }}"></span> Gemini API: {{ '設定済み' if s.gemini_api_key else '未設定' }}</div>
            <div class="status-item"><span class="dot {{ 'dot-green' if s.gmail_app_password else 'dot-red' }}"></span> Gmail: {{ '設定済み' if s.gmail_app_password else '未設定' }}</div>
            <div class="status-item"><span class="dot {{ 'dot-green' if s.schedule_time else 'dot-yellow' }}"></span> 自動実行: {{ '毎日 ' + s.schedule_time if s.schedule_time else '未設定' }}</div>
            <div class="status-item"><span class="dot {{ 'dot-green' if last_run else 'dot-yellow' }}"></span> 最終実行: {{ last_run or '未実行' }}</div>
        </div>
    </div>
</div>
<script>
function togglePw(id) { const el = document.getElementById(id); el.type = el.type === 'password' ? 'text' : 'password'; }
async function runTest() {
    const box = document.getElementById('testResult');
    box.style.display = 'block';
    box.style.background = 'rgba(29,155,240,0.1)'; box.style.border = '1px solid rgba(29,155,240,0.3)'; box.style.color = '#1d9bf0';
    box.textContent = '⏳ テスト実行中... (20〜30秒かかります)';
    try {
        const resp = await fetch('/test', { method: 'POST' });
        const data = await resp.json();
        if (data.success) { box.style.background = 'rgba(0,186,124,0.1)'; box.style.border = '1px solid rgba(0,186,124,0.3)'; box.style.color = '#00ba7c'; }
        else { box.style.background = 'rgba(244,33,46,0.1)'; box.style.border = '1px solid rgba(244,33,46,0.3)'; box.style.color = '#f4212e'; }
        box.textContent = data.message;
    } catch (e) { box.style.background = 'rgba(244,33,46,0.1)'; box.style.color = '#f4212e'; box.textContent = '❌ エラー: ' + e.message; }
}
</script>
</body></html>
"""

# --- ヘルプページテンプレート ---

HELP_TEMPLATE = (
"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>セットアップガイド - Xリスト自動要約</title>
<style>
"""
+ COMMON_CSS +
"""
.back-link { display: inline-block; margin-bottom: 20px; font-size: 14px; }
.section p { color: #c4c8cc; line-height: 1.8; margin-bottom: 12px; font-size: 15px; }
.section h3 { font-size: 16px; color: #1d9bf0; margin: 20px 0 10px; }
.section ol, .section ul { color: #c4c8cc; line-height: 2.0; margin: 8px 0 16px 24px; font-size: 14px; }
.section li { margin-bottom: 6px; }
.section code { background: #202327; padding: 2px 8px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 13px; color: #ffd400; }
.code-block { background: #202327; border: 1px solid #333639; border-radius: 8px; padding: 12px 16px; margin: 8px 0 16px; font-family: 'Consolas', monospace; font-size: 13px; color: #e7e9ea; line-height: 1.6; }
.warn { background: rgba(255,212,0,0.1); border: 1px solid rgba(255,212,0,0.3); border-radius: 8px; padding: 12px 16px; color: #ffd400; font-size: 13px; margin: 12px 0; }
.toc { background: #16181c; border: 1px solid #2f3336; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; }
.toc h3 { color: #e7e9ea; margin: 0 0 12px; font-size: 16px; }
.toc ol { margin: 0 0 0 20px; }
.toc li { margin-bottom: 4px; }
.toc a { font-size: 14px; }
</style>
</head>
<body>
<div class="container">
    <a href="/" class="back-link">← 設定画面に戻る</a>
    <header>
        <h1>📖 セットアップガイド</h1>
        <p>初めての方でもステップごとに設定できます</p>
    </header>
"""
)

HELP_TEMPLATE += """
    <!-- 目次 -->
    <div class="toc">
        <h3>📑 目次</h3>
        <ol>
            <li><a href="#overview">このシステムの仕組み</a></li>
            <li><a href="#prerequisites">始める前に必要なもの</a></li>
            <li><a href="#list">Step 1: XリストURLの取得</a></li>
            <li><a href="#cookies">Step 2: X認証Cookieの取得</a></li>
            <li><a href="#gemini">Step 3: Gemini APIキーの取得</a></li>
            <li><a href="#gmail">Step 4: Gmailアプリパスワードの取得</a></li>
            <li><a href="#test">Step 5: テスト実行</a></li>
            <li><a href="#scheduler">Step 6: 毎日の自動実行（任意）</a></li>
            <li><a href="#troubleshooting">よくあるトラブル</a></li>
        </ol>
    </div>

    <!-- 概要 -->
    <div class="section" id="overview">
        <h2>🔄 このシステムの仕組み</h2>
        <p>以下の3ステップを自動で行います：</p>
        <ol>
            <li><strong>X(Twitter)のリスト</strong>から最新の投稿を取得</li>
            <li><strong>Gemini AI</strong>が内容をカテゴリ別に要約</li>
            <li><strong>Gmail</strong>であなた宛てにメール送信</li>
        </ol>
        <p>毎日1回実行すれば、AIニュースのダイジェストが届きます。</p>
    </div>

    <!-- 前提条件 -->
    <div class="section" id="prerequisites">
        <h2>✅ 始める前に必要なもの</h2>
        <ul>
            <li><strong>Python 3.10以上</strong>（<a href="https://www.python.org/downloads/" target="_blank">ダウンロード</a>）</li>
            <li><strong>X(Twitter)アカウント</strong> — ログインした状態のChromeブラウザ</li>
            <li><strong>Googleアカウント</strong> — Gemini API と Gmail 用</li>
        </ul>
        <p>ライブラリのインストール：</p>
        <div class="code-block">pip install -r requirements.txt</div>
        <div class="warn">⚠️ setup.bat などのバッチファイル実行時に、Windows Defenderなどのウイルス対策ソフトが警告を出す場合があります。これはpip installなどのシステムコマンドがマルウェアと似た動作として誤検知されるためです。ファイルの中身はすべて<a href="https://github.com/gamaken216/x-summary2" target="_blank">GitHub</a>で公開されており安全です。「許可」を選択して続行してください。</div>
    </div>
"""

HELP_TEMPLATE += """
    <!-- Step 1: リストURL -->
    <div class="section" id="list">
        <h2>📱 Step 1: XリストURLの取得</h2>
        <p>X(Twitter)の「リスト」機能で、要約したいアカウントをまとめます。</p>

        <h3>リストがある場合</h3>
        <ol>
            <li>Xにログインし、左メニューから「リスト」をクリック</li>
            <li>要約したいリストを開く</li>
            <li>ブラウザのアドレスバーからURLをコピー</li>
        </ol>
        <div class="code-block">https://x.com/i/lists/1234567890123456789</div>
        <p>末尾の数字がリストIDです。</p>

        <h3>リストを新しく作る場合</h3>
        <ol>
            <li>左メニュー →「リスト」→ 右上の「新しいリストを作成」</li>
            <li>リスト名を入力（例:「AI情報」）。非公開でもOK</li>
            <li>フォローしたいアカウントを追加</li>
            <li>リストページのURLをコピー</li>
        </ol>
    </div>

    <!-- Step 2: Cookie -->
    <div class="section" id="cookies">
        <h2>🍪 Step 2: X認証Cookieの取得</h2>
        <p>Xのリストを読み取るために「Cookie」という認証情報が必要です。3つの値を取得します。</p>
        <div class="warn">⚠️ Cookieはパスワードと同じくらい重要です。他人に教えないでください。</div>

        <h3>取得手順（Chrome）</h3>
        <ol>
            <li>Chromeで <a href="https://x.com" target="_blank">x.com</a> にログインした状態にする</li>
            <li>キーボードの <code>F12</code> を押す（開発者ツールが開きます）</li>
            <li>上のタブから <strong>「Application」</strong> をクリック</li>
            <li>左サイドバーで <strong>「Cookies」→「https://x.com」</strong> をクリック</li>
            <li>表の Name 列から以下を探し、<strong>Value 列の値</strong>をコピー：</li>
        </ol>

        <h3>① auth_token</h3>
        <p>ログイン認証トークン。40文字程度の英数字です。Name列で「auth_token」を探し、Value列をコピーします。</p>

        <h3>② ct0</h3>
        <p>CSRFトークン（セキュリティ用）。長い英数字です。Name列で「ct0」を探し、Value列をコピーします。</p>

        <h3>③ twid</h3>
        <p>あなたのユーザーID。<code>u%3D</code>で始まる文字列です。Name列で「twid」を探し、Value列をコピーします。</p>

        <div class="warn">⚠️ Cookieには有効期限があります（約1年）。期限切れやログアウトで無効になった場合は、同じ手順で再取得してください。</div>
    </div>
"""

HELP_TEMPLATE += """
    <!-- Step 3: Gemini API -->
    <div class="section" id="gemini">
        <h2>🤖 Step 3: Gemini APIキーの取得</h2>
        <p>GoogleのAI「Gemini」でツイートを要約します。APIキーは無料です。</p>
        <ol>
            <li><a href="https://aistudio.google.com/apikey" target="_blank">Google AI Studio</a> にGoogleアカウントでログイン</li>
            <li>「APIキーを作成」（Create API Key）をクリック</li>
            <li>プロジェクトを選択（なければ自動作成）</li>
            <li>生成されたキーをコピー</li>
        </ol>
        <p>キーは <code>AIza</code> で始まる約40文字の文字列です。</p>
        <div class="warn">💡 無料プランでも1日1,500リクエスト使えます。この用途なら十分です。</div>
    </div>

    <!-- Step 4: Gmail -->
    <div class="section" id="gmail">
        <h2>📧 Step 4: Gmailアプリパスワードの取得</h2>
        <p>要約をメール送信するために、Gmail専用の「アプリパスワード」を発行します。</p>

        <h3>① まず2段階認証を有効にする</h3>
        <ol>
            <li><a href="https://myaccount.google.com/security" target="_blank">Googleセキュリティ設定</a> を開く</li>
            <li>「2段階認証プロセス」を有効にする（すでに有効なら次へ）</li>
        </ol>

        <h3>② アプリパスワードを発行</h3>
        <ol>
            <li><a href="https://myaccount.google.com/apppasswords" target="_blank">アプリパスワード設定</a> を開く</li>
            <li>アプリ名を入力（例:「X自動要約」）</li>
            <li>「作成」をクリック</li>
            <li>表示された<strong>16文字のパスワード</strong>をコピー</li>
        </ol>
        <div class="warn">⚠️ このパスワードは一度しか表示されません。コピーし忘れたら再発行してください。スペースは除いて入力します。</div>
    </div>
"""

HELP_TEMPLATE += """
    <!-- Step 5: テスト -->
    <div class="section" id="test">
        <h2>🧪 Step 5: テスト実行</h2>
        <p>すべて入力して「設定を保存」したら：</p>
        <ol>
            <li><a href="/">設定画面</a> の「🧪 テスト実行」ボタンをクリック</li>
            <li>20〜30秒待つと3項目がテストされます：
                <ul>
                    <li>X接続 → ツイート件数が表示される</li>
                    <li>Gemini API → 「OK」と返る</li>
                    <li>Gmail接続 → ログイン成功</li>
                </ul>
            </li>
            <li>すべて ✅ になれば完了！</li>
        </ol>
    </div>

    <!-- Step 6: スケジューラ -->
    <div class="section" id="scheduler">
        <h2>⏰ Step 6: 毎日の自動実行（任意）</h2>
        <p>Windowsのタスクスケジューラで毎日決まった時間に実行できます。</p>
        <ol>
            <li>Windowsの検索バーで「タスクスケジューラ」と入力して開く</li>
            <li>右側の「基本タスクの作成」をクリック</li>
            <li>名前:「X自動要約」→ 次へ</li>
            <li>トリガー:「毎日」→ 好きな時間（例: 08:00）→ 次へ</li>
            <li>操作:「プログラムの開始」→ 次へ</li>
            <li>プログラム: <code>run_daily.bat</code> のフルパスを指定</li>
            <li>開始: <code>run_daily.bat</code> があるフォルダのパスを指定</li>
            <li>完了！</li>
        </ol>
        <h3>バックグラウンドで実行する（推奨）</h3>
        <p>初期設定では実行時にコマンドプロンプトの黒い画面が表示されます。以下の設定で非表示にできます。</p>
        <ol>
            <li>タスクスケジューラで作成したタスク「X自動要約」を右クリック →「プロパティ」</li>
            <li>「全般」タブで <strong>「ユーザーがログオンしているかどうかにかかわらず実行する」</strong> を選択</li>
            <li>「OK」をクリック → Windowsのパスワードを入力</li>
        </ol>
        <p>これで完全にバックグラウンドで動作し、画面に何も表示されなくなります。</p>
    </div>

    <!-- トラブル -->
    <div class="section" id="troubleshooting">
        <h2>🔧 よくあるトラブル</h2>

        <h3>「X接続エラー」が出る</h3>
        <ul>
            <li>Cookieが古い → Xにログインし直してCookieを再取得</li>
            <li>3つのCookieが全部正しいか確認</li>
            <li>値の前後に余分なスペースがないか確認</li>
        </ul>

        <h3>「Gemini APIエラー」が出る</h3>
        <ul>
            <li>APIキーが「AIza」で始まっているか確認</li>
            <li>Google AI Studio でキーが有効か確認</li>
            <li>無料枠を使い切った場合は翌日リセット</li>
        </ul>

        <h3>「Gmail接続エラー」が出る</h3>
        <ul>
            <li>アプリパスワード（16文字）を使っているか確認</li>
            <li>2段階認証が有効になっているか確認</li>
            <li>パスワードにスペースが含まれていないか確認</li>
        </ul>

        <h3>「本日はすでに送信済みです」と出る</h3>
        <p>1日1回の制限です。再テストしたい場合は、フォルダ内の <code>.last_run</code> ファイルを削除してください。</p>
    </div>

    <div style="text-align:center; padding: 32px 0; color: #71767b; font-size: 13px;">
        <a href="/">← 設定画面に戻る</a>
    </div>
</div>
</body></html>
"""


# --- ルート ---

@app.route("/")
def index():
    s = load_settings()
    last_run = None
    last_run_file = os.path.join(SCRIPT_DIR, ".last_run")
    if os.path.exists(last_run_file):
        with open(last_run_file, "r") as f:
            last_run = f.read().strip()
    return render_template_string(HTML_TEMPLATE, s=s, last_run=last_run)


@app.route("/help")
def help_page():
    return render_template_string(HELP_TEMPLATE)


@app.route("/save", methods=["POST"])
def save():
    data = {
        "list_url": request.form.get("list_url", "").strip(),
        "gemini_api_key": request.form.get("gemini_api_key", "").strip(),
        "gmail_user": request.form.get("gmail_user", "").strip(),
        "gmail_app_password": request.form.get("gmail_app_password", "").strip(),
        "schedule_time": request.form.get("schedule_time", "07:00").strip(),
        "x_cookies": {
            "auth_token": request.form.get("auth_token", "").strip(),
            "ct0": request.form.get("ct0", "").strip(),
            "twid": request.form.get("twid", "").strip(),
        }
    }
    save_settings(data)

    # Register task scheduler (background, silent, run if missed)
    schedule_time = data.get("schedule_time", "07:00")
    vbs_path = os.path.join(SCRIPT_DIR, "run_silent.vbs")
    task_name = "X-AutoSummary"
    try:
        import subprocess
        # Use PowerShell to register task with StartWhenAvailable
        hour, minute = schedule_time.split(":")
        ps_script = f'''
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"{vbs_path}"'
$trigger = New-ScheduledTaskTrigger -Daily -At "{schedule_time}"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Description "X List Auto-Summary (daily)" | Out-Null
Write-Output "OK"
'''
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=15
        )
        if "OK" in result.stdout:
            flash(f"✅ 設定を保存しました！（毎日 {schedule_time} に自動実行 ※PC起動時に未実行分も実行）", "success")
        else:
            error_msg = result.stderr.strip()[:100] if result.stderr else "unknown error"
            flash(f"✅ 設定を保存しました！⚠️ スケジューラ登録に失敗: {error_msg}", "success")
    except Exception as e:
        flash(f"✅ 設定を保存しました！⚠️ スケジューラ登録エラー: {e}", "success")

    return redirect(url_for("index"))


@app.route("/test", methods=["POST"])
def test_run():
    results = []
    success = True
    s = load_settings()

    if not s["x_cookies"].get("auth_token"):
        results.append("❌ X Cookie: auth_token が未設定")
        success = False
    else:
        try:
            from twikit import Client as TwikitClient
            client = TwikitClient('ja-JP')
            client.set_cookies(s["x_cookies"])
            list_id = s["list_url"].split("/")[-1]
            tweets = asyncio.run(client.get_list_tweets(list_id))
            results.append(f"✅ X接続OK: {len(tweets)}件のツイート取得")
        except Exception as e:
            results.append(f"❌ X接続エラー: {e}")
            success = False

    if not s["gemini_api_key"]:
        results.append("❌ Gemini APIキーが未設定")
        success = False
    else:
        try:
            from google import genai
            client = genai.Client(api_key=s["gemini_api_key"])
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents='テスト。「OK」とだけ返してください。'
            )
            results.append(f"✅ Gemini API OK: {resp.text[:30]}")
        except Exception as e:
            results.append(f"❌ Gemini APIエラー: {e}")
            success = False

    if not s["gmail_app_password"]:
        results.append("❌ Gmailアプリパスワードが未設定")
        success = False
    else:
        try:
            import smtplib
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(s["gmail_user"], s["gmail_app_password"])
            results.append(f"✅ Gmail接続OK: {s['gmail_user']}")
        except Exception as e:
            results.append(f"❌ Gmail接続エラー: {e}")
            success = False

    return jsonify({"success": success, "message": "\n".join(results)})


# --- 起動 ---

if __name__ == "__main__":
    import webbrowser
    import threading

    print("=" * 50)
    print("Xリスト自動要約システム - 設定画面")
    print("=" * 50)
    print()
    print("ブラウザで http://localhost:5000 を開いています...")
    print("終了するには Ctrl+C を押してください")
    print()

    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
