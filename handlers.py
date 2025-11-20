from telegram.ext import CommandHandler, CallbackQueryHandler
from keyboards import format_session_text, get_session_buttons
import db
import config

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("games", list_games))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CommandHandler("addgame", add_game_cmd))
    app.add_handler(CommandHandler("addsession", add_session_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

# /start
async def start(update, context):
    await update.message.reply_text("Привет! Я бот для записи на настольные игры. Используй /sessions чтобы посмотреть встречи.")

# /games
async def list_games(update, context):
    games = db.list_games()
    if not games:
        await update.message.reply_text("Список игр пуст.")
        return
    text = "Список игр:\n" + "\n".join([f"{g['id']}. {g['name']}" for g in games])
    await update.message.reply_text(text)

# /addgame ADMIN ONLY
async def add_game_cmd(update, context):
    user_id = update.effective_user.id
    if user_id not in config.ADMINS:
        await update.message.reply_text("Только админ может добавлять игры!")
        return
    if not context.args:
        await update.message.reply_text("Используй /addgame Название игры")
        return
    name = " ".join(context.args)
    db.add_game(name)
    await update.message.reply_text(f"Игра '{name}' добавлена ✅")

# /addsession ADMIN ONLY
async def add_session_cmd(update, context):
    user_id = update.effective_user.id
    if user_id not in config.ADMINS:
        await update.message.reply_text("Только админ может создавать встречи!")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Используй /addsession GAME_ID Дата(YYYY-MM-DD) Время(HH:MM) Лимит")
        return
    game_id = int(context.args[0])
    date = context.args[1]
    time = context.args[2]
    limit = int(context.args[3]) if len(context.args) > 3 else 5
    dt_utc = f"{date}T{time}:00+00:00"
    db.add_session(game_id, dt_utc, limit)
    await update.message.reply_text("Встреча создана ✅")

# /sessions
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

# кнопки
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
    # можно расширить edit_ и noop
