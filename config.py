import os
from pathlib import Path

# Token environment variable name (set in Render -> Environment)
TOKEN = os.getenv("TG_BOT_TOKEN")

# Admin Telegram user IDs (replace with yours)
ADMIN_IDS = [200615203]

# Path to SQLite DB file (will be created in the working directory)
DB_PATH = Path("sessions.db")

# Reminder offset in minutes (how long before session to send reminder)
REMINDER_MINUTES = int(os.getenv("REMINDER_MINUTES", "60"))

# Timezone to interpret input datetimes (recommend Europe/Berlin)
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Europe/Moscow")
