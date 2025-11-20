import os
from telegram.ext import ApplicationBuilder
import db
import config
from handlers import register_handlers
from jobs import send_reminder
from datetime import datetime, timezone, timedelta

def schedule_existing_jobs(app):
    """Сканируем будущие сессии в DB и ставим напоминания через JobQueue"""
    sessions = db.list_upcoming_sessions()
    for s in sessions:
        dt = datetime.fromisoformat(s["dt_utc"])
        run_at = dt - timedelta(minutes=config.REMINDER_MINUTES)
        if run_at > datetime.now(timezone.utc):
            app.job_queue.run_once(send_reminder, when=run_at, data={"session_id": s["id"]})

def main():
    TOKEN = os.getenv("TG_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TG_BOT_TOKEN не задан в Environment")

    WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
    PORT = int(os.environ.get("PORT", 10000))

    # Инициализация базы данных
    db.init_db()

    # Создаём приложение
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем все обработчики
    register_handlers(app)

    # Планируем напоминания для существующих сессий
    schedule_existing_jobs(app)

    if not WEBHOOK_URL:
        # Локальный fallback: polling для теста
        print("RENDER_EXTERNAL_URL не найден — запускаем polling")
        app.run_polling()
        return

    # Запуск webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
