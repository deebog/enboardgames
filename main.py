from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import config
from handlers import start, list_sessions, list_games, button_handler

def main():
    # Создаем приложение Telegram
    app = ApplicationBuilder().token(config.TOKEN).build()

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CommandHandler("games", list_games))

    # Регистрируем обработчик всех инлайн-кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    # Запуск long polling
    # ⚠️ Не использовать webhook, не открывать порт
    print("Бот запущен. Ожидание команд...")
    app.run_polling()

if __name__ == "__main__":
    main()
