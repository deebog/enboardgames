import os
from telegram.ext import Application
from handlers import register_handlers
import db
import config

def main():
    TOKEN = os.getenv("TG_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TG_BOT_TOKEN не задан в Environment")

    WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
    PORT = int(os.environ.get("PORT", 10000))

    # Инициализация базы
    db.init_db()

    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    register_handlers(app)

    # Запуск webhook
    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        # локально fallback на polling
        app.run_polling()

if __name__ == "__main__":
    main()
