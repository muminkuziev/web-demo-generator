import os
import base64
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("muminkuziev")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


async def create_repo(repo_name: str):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "name": repo_name,
        "auto_init": False,
        "private": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            return await resp.json()


async def upload_file(repo_name: str, file_content: str):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/index.html"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    encoded = base64.b64encode(file_content.encode()).decode()

    payload = {
        "message": "Upload demo file",
        "content": encoded
    }

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=payload) as resp:
            return await resp.json()


async def enable_pages(repo_name: str):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            return await resp.json()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("HTML/CSS/JS kod yuboring, men uni jonli saytga aylantirib beraman.")


@dp.message()
async def handle_file(message: types.Message):
    if not message.document:
        return await message.answer("Iltimos, HTML fayl yuboring.")

    file = await bot.get_file(message.document.file_id)
    file_path = file.file_path
    file_bytes = await bot.download_file(file_path)
    content = file_bytes.read().decode()

    repo_name = f"demo-{message.from_user.id}"

    await message.answer("⏳ Repo yaratilyapti...")
    await create_repo(repo_name)

    await message.answer("📤 Fayl yuklanyapti...")
    await upload_file(repo_name, content)

    await message.answer("🚀 GitHub Pages yoqilyapti...")
    await enable_pages(repo_name)

    link = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"
    await message.answer(f"✅ Tayyor!\n\nSizning demo saytingiz:\n{link}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
