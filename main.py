import os
from telegram.ext import Application
from handlers import register_handlers
import db

def main():
    TOKEN = os.getenv("TG_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TG_BOT_TOKEN не задан в Environment")

    WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
    PORT = int(os.environ.get("PORT", 10000))

    db.init_db()

    app = Application.builder().token(TOKEN).build()

    register_handlers(app)

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
