from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ADMIN_IDS
from bot.db import get_conn, init_db
from bot.keyboards import games_keyboard, edit_games_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает! Используйте /menu")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:
"
        "/games — список игр
"
        "/editgames — редактировать игры
"
        "/create — создать встречу (админ)"
    )

async def games_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name FROM games")
    games = [row[0] for row in c.fetchall()]
    conn.close()
    if not games:
        await update.message.reply_text("Список игр пуст.")
    else:
        await update.message.reply_text("Игры:
" + "\n".join(games))

async def edit_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Недостаточно прав.")
    await update.message.reply_text("Редактирование игр:", reply_markup=edit_games_keyboard())

async def add_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Недостаточно прав.")
    if len(context.args) == 0:
        return await update.message.reply_text("Использование: /addgame <Название>")
    name = " ".join(context.args)
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO games (name) VALUES (?)", (name,))
        conn.commit()
        await update.message.reply_text(f"Игра '{name}' добавлена.")
    except:
        await update.message.reply_text("Такая игра уже существует!")
    conn.close()

async def delete_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, game_id = query.data.split(":")
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM games WHERE id=?", (game_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text("Игра удалена.")

async def create_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Недостаточно прав.")
    await update.message.reply_text("Создание встречи...
Выберите игру:", reply_markup=games_keyboard())

async def choose_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, game_id = query.data.split(":")
    context.user_data["new_session_game"] = game_id
    await query.edit_message_text("Введите дату (ДД.ММ.ГГГГ):")
