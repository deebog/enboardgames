import os

print("FILES IN WORKING DIR:")
print(os.listdir("."))

import telegram
print("PTB VERSION:", telegram.__version__)

from telegram.ext import ApplicationBuilder
from config import TOKEN
from handlers import register_handlers
from db import init_db

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    register_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()
