import os
import db
import config
from telegram.ext import ApplicationBuilder
from handlers import register_handlers
from jobs import send_reminder
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

def schedule_existing_jobs(app):
    # Scan DB for future sessions and schedule reminders
    rows = db.list_upcoming_sessions()
    for r in rows:
        dt = datetime.fromisoformat(r["dt_utc"])
        run_at = dt - timedelta(minutes=config.REMINDER_MINUTES)
        if run_at > datetime.now(timezone.utc):
            # schedule
            app.job_queue.run_once(send_reminder, when=run_at, data={"session_id": r["id"]})

def main():
    if not config.TOKEN:
        raise RuntimeError("TG_BOT_TOKEN not set in environment.")

    # init DB
    db.init_db()

    app = ApplicationBuilder().token(config.TOKEN).build()

    # register handlers
    register_handlers(app)

    # schedule reminders for existing sessions
    schedule_existing_jobs(app)

    # Run webhook on Render
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if not RENDER_URL:
        # fallback: run polling locally (for dev)
        print("RENDER_EXTERNAL_URL not set — running polling (dev mode)")
        app.run_polling()
        return

    # webhook path — we keep root
    webhook_url = RENDER_URL  # keep it simple, root path

    port = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
