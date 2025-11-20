from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.db import get_conn

def games_keyboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name FROM games")
    games = c.fetchall()
    conn.close()
    buttons = [[InlineKeyboardButton(name, callback_data=f"choose_game:{id}")]
               for id, name in games]
    return InlineKeyboardMarkup(buttons)

def edit_games_keyboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name FROM games")
    games = c.fetchall()
    conn.close()
    buttons = [[InlineKeyboardButton(f"❌ {name}", callback_data=f"delgame:{id}")]
               for id, name in games]
    return InlineKeyboardMarkup(buttons)
