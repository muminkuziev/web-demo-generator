import os
import base64
import threading
import requests
import telebot
from flask import Flask

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
web = Flask(__name__)


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
        "Accept": "application/vnd.github+json"
    }


def create_repo(repo_name):
    url = "https://api.github.com/user/repos"
    data = {
        "name": repo_name,
        "auto_init": True,
        "private": False
    }
    response = requests.post(url, headers=github_headers(), json=data)
    return response.json()


def upload_file(repo_name, content):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/index.html"

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Upload demo index.html",
        "content": encoded,
        "branch": "main"
    }

    response = requests.put(url, headers=github_headers(), json=data)
    return response.json()


def enable_pages(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    response = requests.post(url, headers=github_headers(), json=data)
    return response.json()


def prepare_html(content):
    content = content.strip()

    if "<html" in content.lower() or "<!doctype html" in content.lower():
        return content

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Web Demo</title>
</head>
<body>
{content}
</body>
</html>"""


def make_repo_name(user_id):
    return f"demo-{user_id}"


def process_html(message, content):
    try:
        html_content = prepare_html(content)
        repo_name = make_repo_name(message.from_user.id)

        bot.send_message(message.chat.id, "⏳ GitHub repo yaratilyapti...")
        repo_result = create_repo(repo_name)

        if "message" in repo_result and "already exists" in repo_result["message"].lower():
            bot.send_message(message.chat.id, "ℹ️ Repo oldin yaratilgan. Fayl yangilanmoqda...")

        bot.send_message(message.chat.id, "📤 HTML GitHub'ga yuklanyapti...")
        upload_result = upload_file(repo_name, html_content)

        if "message" in upload_result and "sha" in upload_result["message"].lower():
            bot.send_message(message.chat.id, "⚠️ Fayl oldin mavjud. Hozircha yangi repo nomi kerak bo‘lishi mumkin.")

        bot.send_message(message.chat.id, "🚀 GitHub Pages yoqilyapti...")
        enable_pages(repo_name)

        link = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

        bot.send_message(
            message.chat.id,
            f"✅ Tayyor!\n\nSizning demo saytingiz:\n{link}\n\n⏳ Link 1–2 daqiqada ochilishi mumkin."
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato chiqdi:\n{e}")


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "✅ Web Demo Generator ishga tushdi.\n\n"
        "Menga HTML kodni oddiy xabar qilib yuboring yoki .html fayl yuboring.\n\n"
        "Men uni jonli demo saytga aylantirib beraman."
    )


@bot.message_handler(content_types=["document"])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode("utf-8", errors="ignore")

        process_html(message, content)

    except Exception as e:
        bot.reply_to(message, f"❌ Faylni o‘qishda xato:\n{e}")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    text = message.text.strip()

    if text.startswith("/"):
        return

    if len(text) < 10:
        bot.reply_to(message, "Iltimos, HTML kod yoki .html fayl yuboring.")
        return

    process_html(message, text)


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling()
