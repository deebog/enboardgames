from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import config
from handlers import start, list_sessions, list_games, button_handler

def main():
    app = ApplicationBuilder().token(config.TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CommandHandler("games", list_games))

    # Обработчик всех кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
