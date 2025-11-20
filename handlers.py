from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from keyboards import (
    format_session_text, get_session_buttons, get_add_game_button,
    get_game_selection_buttons, get_global_buttons
)
import db, config
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Conversation states
INPUT_GAME_NAME, SELECT_GAME, INPUT_SESSION_DT, INPUT_SESSION_LIMIT = range(4)
EDIT_SELECT_FIELD, EDIT_INPUT = range(4,6)

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sessions", list_sessions))
    app.add_handler(CommandHandler("games", list_games))
    app.add_handler(CallbackQueryHandler(button_handler))

    conv_addgame = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="addgame")],
        states={INPUT_GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_game_name)]},
        fallbacks=[]
    )
    app.add_handler(conv_addgame)

    conv_addsession = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="addsession")],
        states={
            SELECT_GAME: [CallbackQueryHandler(select_game)],
            INPUT_SESSION_DT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_session_dt)],
            INPUT_SESSION_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_session_limit)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_addsession)

# Команды
async def start(update, context):
    await update.message.reply_text(
        "Привет! Я бот для записи на настольные игры.\n"
        "Используй /sessions чтобы увидеть встречи и /games для списка игр."
    )

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

    # Кнопка "Записаться на все встречи" для обычных пользователей
    kb_all = get_global_buttons(user_id)
    if kb_all.inline_keyboard:
        await update.message.reply_text("Хотите записаться сразу на все встречи?", reply_markup=kb_all)

    # Кнопка "Создать сессию" для админа
    if user_id in config.ADMINS:
        kb_admin = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("➕ Создать сессию", callback_data="addsession")
        ])
        await update.message.reply_text("Админские действия:", reply_markup=kb_admin)

async def list_games(update, context):
    user_id = update.effective_user.id
    games = db.list_games()
    text = "Список игр:\n" + ("\n".join([g['name'] for g in games]) if games else "(пусто)")

    kb = get_add_game_button() if user_id in config.ADMINS else None
    await update.message.reply_text(text, reply_markup=kb)

# Обработчик кнопок
async def button_handler(update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    if data == "addgame":
        await query.message.reply_text("Введите название новой игры:")
        return INPUT_GAME_NAME

    if data == "addsession":
        games = db.list_games()
        if not games:
            await query.message.reply_text("Сначала добавьте игры через /games")
            return ConversationHandler.END
        await query.message.reply_text("Выберите игру для новой сессии:", reply_markup=get_game_selection_buttons(games))
        return SELECT_GAME

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

    elif data == "join_all":
        sessions = db.list_upcoming_sessions()
        added_count = 0
        for s in sessions:
            if user.username not in s['participants'] and len(s['participants']) < s['limit']:
                db.add_participant(s['id'], user.username)
                added_count += 1
        await query.answer(f"Вы записаны на {added_count} встреч(и) ✅", show_alert=True)
