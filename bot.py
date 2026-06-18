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
    return "Web Demo Generator is running"

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
    return requests.post(url, headers=github_headers(), json=data).json()

def upload_file(repo_name, content):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/index.html"

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Upload demo index.html",
        "content": encoded,
        "branch": "main"
    }

    return requests.put(url, headers=github_headers(), json=data).json()

def enable_pages(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    return requests.post(url, headers=github_headers(), json=data).json()

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "✅ HTML fayl yuboring. Men uni jonli demo saytga aylantirib beraman."
    )

@bot.message_handler(content_types=["document"])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        content = downloaded_file.decode("utf-8", errors="ignore")

        repo_name = f"demo-{message.from_user.id}"

        bot.reply_to(message, "⏳ GitHub repo yaratilyapti...")
        create_repo(repo_name)

        bot.send_message(message.chat.id, "📤 HTML fayl yuklanyapti...")
        upload_file(repo_name, content)

        bot.send_message(message.chat.id, "🚀 GitHub Pages yoqilyapti...")
        enable_pages(repo_name)

        link = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

        bot.send_message(
            message.chat.id,
            f"✅ Tayyor!\n\nSizning demo saytingiz:\n{link}\n\n⏳ Link 1-2 daqiqada ochilishi mumkin."
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Xato chiqdi:\n{e}")

@bot.message_handler(func=lambda message: True)
def other(message):
    bot.reply_to(message, "Iltimos, HTML fayl yuboring.")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling()
