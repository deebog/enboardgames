from telegram.ext import ContextTypes
import datetime

async def reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Напоминание о встрече: {job.data}")
