from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def main_menu_buttons():
    buttons = [
        [InlineKeyboardButton("📋 Список сессий", callback_data="show_sessions")],
        [InlineKeyboardButton("🗂️ Мои записи", callback_data="my_sessions")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_add_game_button():
    return InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("➕ Добавить игру", callback_data="addgame")
    ])

def get_game_selection_buttons(games):
    buttons = [InlineKeyboardButton(g['name'], callback_data=f"selgame_{g['id']}") for g in games]
    return InlineKeyboardMarkup.from_column(buttons)

def format_session_text(session):
    participants = ", ".join(session['participants']) if session['participants'] else "(пусто)"
    free_slots = session['limit'] - len(session['participants'])
    dt = session['dt'].replace("T", " ")
    return f"🗓 {dt}\n🎲 {session['game']}\n👥 {len(session['participants'])}/{session['limit']}\nЗаписаны: {participants}\nСвободно мест: {free_slots}"

def get_session_buttons(session, user_id):
    buttons = []
    username = str(user_id)
    if username not in session['participants'] and len(session['participants']) < session['limit']:
        buttons.append(InlineKeyboardButton("✅ Записаться", callback_data=f"join_{session['id']}"))
    if username in session['participants']:
        buttons.append(InlineKeyboardButton("❌ Отписаться", callback_data=f"leave_{session['id']}"))
    if user_id in config.ADMINS:
        buttons.append(InlineKeyboardButton("🗑 Удалить сессию", callback_data=f"delete_{session['id']}"))
    return InlineKeyboardMarkup.from_row(buttons)

def get_global_buttons(user_id):
    return InlineKeyboardMarkup.from_row([InlineKeyboardButton("➕ Записаться на все встречи", callback_data="join_all")])
