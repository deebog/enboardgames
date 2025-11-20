from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Этот бот записывает игроков на настольные игры."
    )

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
