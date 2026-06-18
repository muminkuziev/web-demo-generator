from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8897379935:AAEsHaBuTAsJKWMRC1aylopO5YCDvGzFUj4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Web Demo Generator ishga tushdi!"
    )

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()
