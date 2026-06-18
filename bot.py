import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

BOT_TOKEN = "8948309691:AAFajuDxUjVEYW4kNrvzvxbuVsXusEh0oHc"

async def start(update, context):
    await update.message.reply_text("✅ Web Demo Generator bot ishlayapti!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
