from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from bot.handlers import start, menu, games_list, edit_games, add_game,     delete_game_callback, create_session, choose_game_callback
from bot.db import init_db
from bot.config import TOKEN

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("games", games_list))
    app.add_handler(CommandHandler("editgames", edit_games))
    app.add_handler(CommandHandler("addgame", add_game))
    app.add_handler(CommandHandler("create", create_session))

    app.add_handler(CallbackQueryHandler(delete_game_callback, pattern="^delgame:"))
    app.add_handler(CallbackQueryHandler(choose_game_callback, pattern="^choose_game:"))

    app.run_polling()

if __name__ == "__main__":
    main()
