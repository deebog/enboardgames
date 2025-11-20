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
        entry_points=[CallbackQueryHandler(add_game_start, pattern="addgame")],
        states={INPUT_GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_game_name)]},
        fallbacks=[]
    )
    app.add_handler(conv_addgame)

    conv_addsession = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_session_start, pattern="addsession")],
        states={
            SELECT_GAME: [CallbackQueryHandler(select_game)],
            INPUT_SESSION_DT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_session_dt)],
            INPUT_SESSION_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_session_limit)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_addsession)

    conv_edit = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_start, pattern="edit_")],
        states={
            EDIT_SELECT_FIELD: [CallbackQueryHandler(edit_select_field, pattern="^field_")],
            EDIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_input)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_edit)

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

    # Для обычных пользователей кнопка "Записаться на все встречи"
    kb_all = get_global_buttons(user_id)
    if kb_all.inline_keyboard:
        await update.message.reply_text("Хотите записаться сразу на все встречи?", reply_markup=kb_all)

    # Для админа кнопка "Создать сессию"
    if user_id in config.ADMINS:
        from keyboards import InlineKeyboardButton, InlineKeyboardMarkup
        kb_admin = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("➕ Создать сессию", callback_data="addsession")
        ])
        await update.message.reply_text("Админские действия:", reply_markup=kb_admin)


async def list_games(update, context):
    user_id = update.effective_user.id
    games = db.list_games()
    text = "Список игр:\n" + ("\n".join([g['name'] for g in games]) if games else "(пусто)")

    kb = None
    if user_id in config.ADMINS:
        # добавляем кнопку "Добавить игру"
        kb = get_add_game_button()
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

# Создание сессии
async def add_session_start(update, context):
    games = db.list_games()
    if not games:
        await update.callback_query.message.reply_text("Сначала добавьте игры через /games")
        return ConversationHandler.END
    await update.callback_query.message.reply_text("Выберите игру для новой сессии:", reply_markup=get_game_selection_buttons(games))
    return SELECT_GAME

async def select_game(update, context):
    query = update.callback_query
    await query.answer()
    game_id = int(query.data.split("_")[1])
    context.user_data['new_session_game_id'] = game_id
    await query.edit_message_text("Введите дату и время сессии в формате YYYY-MM-DD HH:MM (UTC):")
    return INPUT_SESSION_DT

async def input_session_dt(update, context):
    dt_text = update.message.text.strip()
    try:
        dt_obj = datetime.strptime(dt_text, "%Y-%m-%d %H:%M")
        context.user_data['new_session_dt'] = dt_obj.isoformat()
        await update.message.reply_text("Введите лимит участников:")
        return INPUT_SESSION_LIMIT
    except:
        await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (YYYY-MM-DD HH:MM):")
        return INPUT_SESSION_DT

async def input_session_limit(update, context):
    try:
        limit = int(update.message.text.strip())
        game_id = context.user_data['new_session_game_id']
        dt_utc = context.user_data['new_session_dt']
        db.add_session(game_id, dt_utc, limit)
        await update.message.reply_text("Сессия создана ✅")
    except:
        await update.message.reply_text("Неверный лимит. Попробуйте еще раз:")
        return INPUT_SESSION_LIMIT
    return ConversationHandler.END

# Редактирование сессии
async def edit_start(update, context):
    query = update.callback_query
    await query.answer()
    session_id = int(query.data.split("_")[1])
    context.user_data['edit_session_id'] = session_id
    keyboard = [
        [InlineKeyboardButton("🎲 Изменить игру", callback_data="field_game")],
        [InlineKeyboardButton("📅 Изменить дату и время", callback_data="field_dt")],
        [InlineKeyboardButton("👥 Изменить лимит", callback_data="field_limit")]
    ]
    await query.edit_message_text("Выберите поле для редактирования:", reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_SELECT_FIELD

async def edit_select_field(update, context):
    query = update.callback_query
    await query.answer()
    field = query.data.split("_")[1]
    context.user_data['edit_field'] = field
    if field == "game":
        games = db.list_games()
        await query.edit_message_text("Выберите новую игру:", reply_markup=get_game_selection_buttons(games))
        return EDIT_INPUT
    else:
        await query.edit_message_text(f"Введите новое значение для {field}:")
        return EDIT_INPUT

async def edit_input(update, context):
    session_id = context.user_data['edit_session_id']
    field = context.user_data['edit_field']
    value = update.message.text.strip()
    if field == "dt":
        try:
            dt_obj = datetime.strptime(value, "%Y-%m-%d %H:%M")
            db.update_session(session_id, dt_utc=dt_obj.isoformat())
        except:
            await update.message.reply_text("Неверный формат даты. Попробуйте YYYY-MM-DD HH:MM")
            return EDIT_INPUT
    elif field == "limit":
        try:
            db.update_session(session_id, limit=int(value))
        except:
            await update.message.reply_text("Неверный лимит. Введите число")
            return EDIT_INPUT
    elif field == "game":
        db.update_session(session_id, game_id=int(value))
    await update.message.reply_text("Сессия обновлена ✅")
    return ConversationHandler.END

# Кнопки join/leave/delete/edit/join_all
async def button_handler(update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data
    
    # Добавляем новый обработчик для создания игры и сессии
    if data == "addgame":
        await query.message.reply_text("Введите название новой игры:")
        return INPUT_GAME_NAME

    if data == "addsession":
        games = db.list_games()
        if not games:
            await query.message.reply_text("Сначала добавьте игры через /games")
            return
        from keyboards import get_game_selection_buttons
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
