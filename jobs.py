from telegram.ext import ContextTypes
import db
import config
from datetime import datetime, timezone

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data or {}
    session_id = data.get("session_id")
    session = db.get_session(session_id)
    if not session:
        return
    # notify all participants who have reminders enabled
    participants = db.list_participants(session_id)
    text = f"Напоминание: встреча по игре {session['game_name']} через {config.REMINDER_MINUTES} минут.\nВремя (UTC): {session['dt_utc']}"
    for uid in participants:
        if db.get_user_reminders(uid):
            try:
                await context.bot.send_message(chat_id=uid, text=text)
            except Exception:
                pass
