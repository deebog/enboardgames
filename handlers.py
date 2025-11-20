from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import db
import config
import keyboards
from datetime import datetime
from zoneinfo import ZoneInfo

# Conversation states for creating a session
(CREATE_WAIT_DATE, CREATE_WAIT_LIMIT) = range(2)

# Helpers
def is_admin(user_id: int):
    return user_id in config.ADMIN_IDS

def parse_datetime_input(text: str):
    """
    Expect format: YYYY-MM-DD HH:MM
    Interpret in DEFAULT_TZ and return UTC ISO string.
    """
    try:
        dt_naive = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
        tz = ZoneInfo(config.DEFAULT_TZ)
        dt_local = dt_naive.replace(tzinfo=tz)
        dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
        return dt_utc.isoformat()
    except Exception:
        return None

# Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для записи на партии по настольным играм.\n/ menu для меню")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Команды:\n"
        "/games — список игр\n"
        "/sessions — список встреч\n"
        "/reminder — переключить личные напоминания\n\n"
        "Для администраторов:\n"
        "/addgame <Название> — добавить игру\n"
        "/delgame <ID> — удалить игру\n"
        "/editgames — визуально редактировать список игр\n"
        "/create — создать встречу (интерактивно)\n"
    )
    await update.message.reply_text(text)

# Games management
async def games_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_games()
    if not rows:
        await update.message.reply_text("Список игр пуст.")
    else:
        lines = [f"{r['id']}: {r['name']}" for r in rows]
        await update.message.reply_text("Игры:\n" + "\n".join(lines))

async def addgame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Только админ может добавлять игры.")
    if not context.args:
        return await update.message.reply_text("Использование: /addgame Название игры")
    name = " ".join(context.args)
    ok = db.add_game(name)
    await update.message.reply_text("Добавлено." if ok else "Ошибка: такая игра уже есть.")

async def delgame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Только админ может удалять игры.")
    if not context.args:
        return await update.message.reply_text("Использование: /delgame ID_игры")
    try:
        gid = int(context.args[0])
    except:
        return await update.message.reply_text("ID должен быть числом.")
    db.delete_game_by_id(gid)
    await update.message.reply_text("Удалено (если существовало).")

async def editgames_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Только админ может редактировать.")
    await update.message.reply_text("Редактирование игр:", reply_markup=keyboards.edit_games_keyboard())

async def del_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, gid = query.data.split(":")
    db.delete_game_by_id(int(gid))
    await query.edit_message_text("Игра удалена.")

# Sessions (meetings)
async def sessions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_upcoming_sessions()
    if not rows:
        return await update.message.reply_text("Нет запланированных встреч.")
    texts = []
    for r in rows:
        cnt = db.participant_count(r["id"])
        texts.append(f"ID:{r['id']} — {r['game_name']} — {r['dt_utc']} — {cnt}/{r['limit_count']}")
    await update.message.reply_text("\n".join(texts))

async def session_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, sid = query.data.split(":")
    sid = int(sid)
    s = db.get_session(sid)
    if not s:
        return await query.edit_message_text("Встреча не найдена.")
    participants = db.list_participants(sid)
    is_joined = query.from_user.id in participants
    can_join = len(participants) < s["limit_count"]
    text = f"Игра: {s['game_name']}\nВремя (UTC): {s['dt_utc']}\nУчастников: {len(participants)}/{s['limit_count']}\nID:{s['id']}"
    kb = keyboards.session_actions_keyboard(sid, query.from_user.id, is_joined, can_join)
    await query.edit_message_text(text, reply_markup=kb)

async def join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, sid = query.data.split(":")
    sid = int(sid)
    s = db.get_session(sid)
    if not s:
        return await query.answer("Встреча не найдена.", show_alert=True)
    if db.participant_count(sid) >= s["limit_count"]:
        return await query.answer("Лимит достигнут.", show_alert=True)
    ok = db.add_participant(sid, query.from_user.id)
    if not ok:
        return await query.answer("Вы уже записаны.", show_alert=True)
    await query.answer("Вы записаны.")
    await session_view_callback(update, context)

async def leave_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, sid = query.data.split(":")
    sid = int(sid)
    db.remove_participant(sid, query.from_user.id)
    await query.answer("Вы выписаны.")
    await session_view_callback(update, context)

async def refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # same as view
    await session_view_callback(update, context)

# Toggle reminders per user
async def reminder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = db.get_user_reminders(uid)
    db.set_user_reminders(uid, not cur)
    await update.message.reply_text(f"Напоминания {'включены' if not cur else 'выключены'}.")

# Creation flow (ConversationHandler)
async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Только админ может создавать встречи.")
    games = db.list_games()
    if not games:
        return await update.message.reply_text("Список игр пуст. Добавьте игру командой /addgame")
    await update.message.reply_text("Выберите игру:", reply_markup=keyboards.games_keyboard())
    return CREATE_WAIT_DATE

async def pick_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, gid = query.data.split(":")
    context.user_data["new_session_game_id"] = int(gid)
    await query.message.reply_text(f"Выбрана игра. Введите дату и время в формате: YYYY-MM-DD HH:MM (в часовом поясе {config.DEFAULT_TZ})")
    return CREATE_WAIT_LIMIT

async def create_receive_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    dt_iso = parse_datetime_input(text)
    if not dt_iso:
        return await update.message.reply_text("Неверный формат. Попробуйте ещё раз: YYYY-MM-DD HH:MM")
    context.user_data["new_session_dt_utc"] = dt_iso
    await update.message.reply_text("Введите лимит участников (число):")
    return ConversationHandler.END  # we'll handle limit in the next message handler below

# Because we ended conversation above, handle limit via a MessageHandler that checks user_data
async def create_receive_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "new_session_dt_utc" not in context.user_data or "new_session_game_id" not in context.user_data:
        return  # not in creation flow
    try:
        limit = int(update.message.text.strip())
    except:
        return await update.message.reply_text("Лимит должен быть числом. Введите снова:")
    gid = context.user_data.pop("new_session_game_id")
    dt_iso = context.user_data.pop("new_session_dt_utc")
    uid = update.effective_user.id
    sid = db.add_session(gid, dt_iso, limit, uid)
    # schedule reminder (JobQueue is added in main)
    # store session id in ctx so main can schedule when handler returns (we will return info)
    await update.message.reply_text(f"Создана встреча ID:{sid}")
    # create job via app.job_queue is done in main when session created - we'll expose this via a callback in main
    # but here we also try to schedule if app present
    try:
        job_queue = context.application.job_queue
        from jobs import send_reminder
        from datetime import datetime, timedelta, timezone
        dt = datetime.fromisoformat(dt_iso)
        run_at = dt - timedelta(minutes=config.REMINDER_MINUTES)
        if run_at.timestamp() > datetime.now(timezone.utc).timestamp():
            job_queue.run_once(send_reminder, when=run_at, data={"session_id": sid})
    except Exception:
        pass

# Register handlers function
def register_handlers(app):
    # basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("games", games_cmd))
    app.add_handler(CommandHandler("sessions", sessions_cmd))
    app.add_handler(CommandHandler("addgame", addgame_cmd))
    app.add_handler(CommandHandler("delgame", delgame_cmd))
    app.add_handler(CommandHandler("editgames", editgames_cmd))
    app.add_handler(CommandHandler("reminder", reminder_cmd))

    # session view and actions
    app.add_handler(CallbackQueryHandler(session_view_callback, pattern=r'^view_session:'))
    app.add_handler(CallbackQueryHandler(join_callback, pattern=r'^join:'))
    app.add_handler(CallbackQueryHandler(leave_callback, pattern=r'^leave:'))
    app.add_handler(CallbackQueryHandler(refresh_callback, pattern=r'^refresh:'))

    # games edit callbacks
    app.add_handler(CallbackQueryHandler(del_game_callback, pattern=r'^del_game:'))

    # creation flow
    conv = ConversationHandler(
        entry_points=[CommandHandler("create", create_start)],
        states={
            CREATE_WAIT_DATE: [CallbackQueryHandler(pick_game_callback, pattern=r'^pick_game:')],
            CREATE_WAIT_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_receive_datetime)],
        },
        fallbacks=[]
    )
    app.add_handler(conv)

    # separate handler to catch limit after date (not in conversation states for simplicity)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, create_receive_limit))
