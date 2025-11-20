from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from keyboards import (
    main_menu_buttons, format_session_text, get_session_buttons,
    get_add_game_button, get_game_selection_buttons, get_global_buttons
)
import db, config

INPUT_GAME_NAME, SELECT_GAME, INPUT_SESSION_DT, INPUT_SESSION_LIMIT = range(4)

async def start(update, context):
    await update.message.reply_text(
        "Привет! Я бот для записи на настольные игры.\nВыберите действие:",
        reply_markup=main_menu_buttons()
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

    kb_all = get_global_buttons(user_id)
    if kb_all.inline_keyboard:
        await update.message.reply_text("Хотите записаться сразу на все встречи?", reply_markup=kb_all)

async def list_games(update, context):
    user_id = update.effective_user.id
    games = db.list_games()
    text = "Список игр:\n" + ("\n".join([g['name'] for g in games]) if games else "(пусто)")
    kb = get_add_game_button() if user_id in config.ADMINS else None
    await update.message.reply_text(text, reply_markup=kb)

async def button_handler(update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    if data == "show_sessions":
        await list_sessions(update, context)
        return

    elif data == "my_sessions":
        sessions = db.list_upcoming_sessions()
        my_sessions = [s for s in sessions if user.username in s['participants']]
        if not my_sessions:
            await query.message.reply_text("Вы пока ни на одной встрече не записаны.")
        else:
            for s in my_sessions:
                await query.message.reply_text(format_session_text(s), reply_markup=get_session_buttons(s, user.id))
        return

    elif data == "addgame":
        await query.message.reply_text("Введите название новой игры:")
        return INPUT_GAME_NAME

    elif data.startswith("join_"):
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
        return
