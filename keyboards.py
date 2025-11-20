from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import db
import config

def format_session_text(session):
    dt_str = session['dt_utc'].replace('T', ' ').split('+')[0]
    participants = ', '.join(session['participants']) if session['participants'] else 'Никто'
    remaining = session['limit'] - len(session['participants'])
    text = (
        f"📅 {dt_str}\n"
        f"🎲 Игра: {session['game']}\n"
        f"👥 Участники: {participants} ({remaining} свободно из {session['limit']})"
    )
    return text

def get_session_buttons(session, user_id):
    buttons = []
    is_admin = user_id in config.ADMINS
    if user_id in [p for p in session['participants']]:
        buttons.append(InlineKeyboardButton("❌ Отписаться", callback_data=f"leave_{session['id']}"))
    elif len(session['participants']) < session['limit']:
        buttons.append(InlineKeyboardButton("✅ Записаться", callback_data=f"join_{session['id']}"))
    else:
        buttons.append(InlineKeyboardButton("❌ Мест нет", callback_data="noop"))

    if is_admin:
        buttons.append(InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{session['id']}"))
        buttons.append(InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{session['id']}"))

    return InlineKeyboardMarkup.from_row(buttons)
