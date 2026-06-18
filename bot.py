import os
import re
import time
import uuid
import base64
import threading
import requests
import telebot
from flask import Flask

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
web = Flask(__name__)
busy_users = set()


@web.route("/")
def home():
    return "✅ Web Demo Generator is running"


@web.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.getenv("PORT", 10000))
    web.run(host="0.0.0.0", port=port)


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def safe_repo_name(user_id):
    unique = int(time.time())
    short = uuid.uuid4().hex[:5]
    return f"demo-{user_id}-{unique}-{short}"


def prepare_html(content):
    content = content.strip()

    if "<html" in content.lower() or "<!doctype html" in content.lower():
        return content

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Web Demo</title>
</head>
<body>
{content}
</body>
</html>"""


def create_repo(repo_name):
    url = "https://api.github.com/user/repos"
    data = {
        "name": repo_name,
        "private": False,
        "auto_init": True,
    }

    r = requests.post(url, headers=github_headers(), json=data, timeout=30)

    if r.status_code not in [201, 202]:
        raise Exception(f"GitHub repo yaratishda xato: {r.status_code} {r.text}")

    return r.json()


def upload_index(repo_name, html):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/index.html"

    encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Upload index.html",
        "content": encoded,
        "branch": "main",
    }

    r = requests.put(url, headers=github_headers(), json=data, timeout=30)

    if r.status_code not in [200, 201]:
        raise Exception(f"HTML yuklashda xato: {r.status_code} {r.text}")

    return r.json()


def enable_pages(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"

    data = {
        "source": {
            "branch": "main",
            "path": "/",
        }
    }

    r = requests.post(url, headers=github_headers(), json=data, timeout=30)

    if r.status_code not in [201, 202, 204]:
        if "already exists" not in r.text.lower():
            raise Exception(f"GitHub Pages yoqishda xato: {r.status_code} {r.text}")

    return True


def is_probably_html(text):
    text_lower = text.lower()
    return (
        "<html" in text_lower
        or "<!doctype html" in text_lower
        or "<body" in text_lower
        or "<h1" in text_lower
        or "<div" in text_lower
        or "<style" in text_lower
    )


def process_html(message, raw_content):
    user_id = message.from_user.id

    if user_id in busy_users:
        bot.send_message(message.chat.id, "⏳ Oldingi demo hali tayyorlanmoqda. Iltimos, biroz kuting.")
        return

    busy_users.add(user_id)

    try:
        html = prepare_html(raw_content)
        repo_name = safe_repo_name(user_id)

        bot.send_message(message.chat.id, "⏳ GitHub repo yaratilmoqda...")
        create_repo(repo_name)

        bot.send_message(message.chat.id, "📤 HTML GitHub'ga yuklanmoqda...")
        upload_index(repo_name, html)

        bot.send_message(message.chat.id, "🚀 GitHub Pages yoqilmoqda...")
        enable_pages(repo_name)

        link = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

        bot.send_message(
            message.chat.id,
            f"✅ <b>Tayyor!</b>\n\n"
            f"🌐 Demo sayt:\n{link}\n\n"
            f"⏳ Link 1–3 daqiqada to‘liq ochiladi."
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato:\n<code>{str(e)}</code>")

    finally:
        busy_users.discard(user_id)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "✅ <b>Web Demo Generator ishga tushdi.</b>\n\n"
        "Menga HTML kodni oddiy xabar qilib yuboring yoki <b>.html</b> fayl yuboring.\n\n"
        "Men uni GitHub Pages orqali jonli demo saytga aylantirib beraman."
    )


@bot.message_handler(content_types=["document"])
def handle_document(message):
    try:
        filename = message.document.file_name or ""

        if not filename.lower().endswith((".html", ".htm", ".txt")):
            bot.reply_to(message, "❌ Faqat .html, .htm yoki .txt fayl yuboring.")
            return

        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode("utf-8", errors="ignore")

        if not content.strip():
            bot.reply_to(message, "❌ Fayl bo‘sh.")
            return

        process_html(message, content)

    except Exception as e:
        bot.reply_to(message, f"❌ Faylni o‘qishda xato:\n{e}")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    text = message.text.strip()

    if text.startswith("/"):
        return

    if len(text) < 10:
        bot.reply_to(message, "❌ HTML kod yoki .html fayl yuboring.")
        return

    if len(text) > 3500:
        bot.reply_to(
            message,
            "⚠️ HTML juda uzun. Uni <b>index.html</b> fayl qilib yuboring.\n\n"
            "Telegram uzun kodni bo‘laklab yuboradi, sayt buzilib qoladi."
        )
        return

    if not is_probably_html(text):
        bot.reply_to(message, "❌ Bu HTML kodga o‘xshamayapti. HTML kod yoki .html fayl yuboring.")
        return

    process_html(message, text)


if __name__ == "__main__":
    print("✅ Web server starting...")
    threading.Thread(target=run_web, daemon=True).start()

    print("✅ Telegram bot polling started...")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
