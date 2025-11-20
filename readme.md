# Telegram Board Game Bot (Full)

Файлы: main.py, handlers.py, db.py, keyboards.py, jobs.py, config.py, requirements.txt

1) Добавьте репозиторий на GitHub.
2) В Render создайте Web Service, подключите репо.
3) В Render -> Environment добавьте:
   - TG_BOT_TOKEN = <токен от BotFather>
   - (опционально) REMINDER_MINUTES, DEFAULT_TZ
4) Build command: pip install -r requirements.txt
   Start command: python main.py
5) Deploy.

Админ: в config.py добавьте свой Telegram user id в ADMIN_IDS.
