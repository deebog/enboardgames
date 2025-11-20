from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from keyboards import format_session_text, get_session_buttons, get_game_buttons
import db
import config

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("games", list_games))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CallbackQueryHandler(button_handler))

async def start(update, context):
    await update.message.reply_text("Привет! Я бот для записи на настольные игры.\n"
                                    "Используй /sessions чтобы увидеть встречи и /games для списка игр.")

# Список игр
async def list_games(update, context):
    user_id = update.effective_user.id
    games = db.list_games()
    if not games:
        await update.message.reply_text("Список игр пуст.")
        return
    for g in games:
        kb = get_game_buttons(g['id']) if user_id in config.ADMINS else None
        await update.message.reply_text(g['name'], reply_markup=kb)

# Список сессий
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

# Кнопки join/leave/edit/delete
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

    elif data.startswith("edit_") and user.id in config.ADMINS:
        await query.edit_message_text("Редактирование сессии (пока упрощённо)")

    elif data.startswith("deletegame_") and user.id in config.ADMINS:
        game_id = int(data.split("_")[1])
        db.delete_game(game_id)
        await query.edit_message_text("Игра удалена ✅")

    elif data.startswith("editgame_") and user.id in config.ADMINS:
        await query.edit_message_text("Редактирование игры (пока упрощённо)")
