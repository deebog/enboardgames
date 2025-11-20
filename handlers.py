from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from keyboards import format_session_text, get_session_buttons, get_add_game_button
import db, config

# Состояние ConversationHandler для добавления игры
INPUT_GAME_NAME = range(1)

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CommandHandler("games", list_games))
    app.add_handler(CallbackQueryHandler(button_handler))

    # ConversationHandler для добавления игры
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_game_start, pattern="addgame")],
        states={INPUT_GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_game_name)]},
        fallbacks=[]
    )
    app.add_handler(conv)

async def start(update, context):
    await update.message.reply_text("Привет! Я бот для записи на настольные игры.\n"
                                    "Используй /sessions чтобы увидеть встречи и /games для списка игр.")

async def list_sessions(update, context):
    user_id = update.effective_user.id
    sessions = db.list_upcoming_sessions()
    if not sessions:
        await update.message.reply_text("Нет предстоящих встреч.")
        return
    for s in sessions:
        text = format_session_text(s)
        kb = get_session_buttons(s, user_id)
        await update.message.reply_text(text, reply_markup=kb)

async def list_games(update, context):
    user_id = update.effective_user.id
    games = db.list_games()
    if not games:
        await update.message.reply_text("Список игр пуст.")
        return

    text = "Список игр:\n" + "\n".join([g['name'] for g in games])
    if user_id in config.ADMINS:
        kb = get_add_game_button()
    else:
        kb = None
    await update.message.reply_text(text, reply_markup=kb)

# Добавление игры
async def add_game_start(update, context):
    await update.callback_query.message.reply_text("Введите название новой игры:")
    return INPUT_GAME_NAME

async def add_game_name(update, context):
    name = update.message.text.strip()
    db.add_game(name)
    await update.message.reply_text(f"Игра '{name}' добавлена ✅")
    return ConversationHandler.END

# Кнопки сессий
async def button_handler(update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    if data.startswith("join_"):
        session_id = int(data.split("_")[1])
        db.add_participant(session_id, user.username)
        session = db.get_session(session_id)
        await query.edit_message_reply_markup(reply_markup=get_session_buttons(session, user.id))

    elif data.startswith("leave_"):
        session_id = int(data.split("_")[1])
        db.remove_participant(session_id, user.username)
        session = db.get_session(session_id)
        await query.edit_message_reply_markup(reply_markup=get_session_buttons(session, user.id))

    elif data.startswith("delete_") and user.id in config.ADMINS:
        session_id = int(data.split("_")[1])
        db.delete_session(session_id)
        await query.edit_message_text("Встреча удалена ✅")
