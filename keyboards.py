from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def format_session_text(session):
    dt_str = session['dt_utc'].replace('T', ' ').split('+')[0]
    participants = ', '.join(session['participants']) if session['participants'] else 'Никто'
    remaining = session['limit'] - len(session['participants'])
    return (
        f"📅 {dt_str}\n"
        f"🎲 Игра: {session['game']}\n"
        f"👥 Участники: {participants} ({remaining} свободно из {session['limit']})"
    )

def get_session_buttons(session, user_id):
    buttons = []
    is_admin = user_id in config.ADMINS

    if user_id in session['participants']:
        buttons.append(InlineKeyboardButton("❌ Отписаться", callback_data=f"leave_{session['id']}"))
    elif len(session['participants']) < session['limit']:
        buttons.append(InlineKeyboardButton("✅ Записаться", callback_data=f"join_{session['id']}"))
    else:
        buttons.append(InlineKeyboardButton("❌ Мест нет", callback_data="noop"))

    if is_admin:
        buttons.append(InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_{session['id']}"))
        buttons.append(InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{session['id']}"))
        buttons.append(InlineKeyboardButton("➕ Создать сессию", callback_data="addsession"))

    return InlineKeyboardMarkup.from_row(buttons)

def get_global_buttons(user_id):
    buttons = []
    if user_id not in config.ADMINS:
        buttons.append(InlineKeyboardButton("📝 Записаться на все встречи", callback_data="join_all"))
    return InlineKeyboardMarkup.from_row(buttons)

def get_add_game_button():
    return InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("➕ Добавить игру", callback_data="addgame")
    ])

def get_game_selection_buttons(games):
    buttons = [InlineKeyboardButton(g['name'], callback_data=f"selgame_{g['id']}") for g in games]
    return InlineKeyboardMarkup.from_column(buttons)
