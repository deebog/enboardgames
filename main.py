from telegram.ext import ApplicationBuilder
import config
from handlers import start, list_sessions, list_games, button_handler

def main():
    app = ApplicationBuilder().token(config.TOKEN).build()

    app.add_handler(start)
    app.add_handler(list_sessions)
    app.add_handler(list_games)
    app.add_handler(button_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
