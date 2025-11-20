from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import db

def games_keyboard():
    rows = []
    for g in db.list_games():
        rows.append([InlineKeyboardButton(g["name"], callback_data=f"pick_game:{g['id']}")])
    return InlineKeyboardMarkup(rows)

def edit_games_keyboard():
    rows = []
    for g in db.list_games():
        rows.append([InlineKeyboardButton(f"❌ {g['name']}", callback_data=f"del_game:{g['id']}")])
    rows.append([InlineKeyboardButton("➕ Добавить игру (командой /addgame)", callback_data="add_game")])
    return InlineKeyboardMarkup(rows)

def session_actions_keyboard(session_id: int, user_id: int, is_joined: bool, can_join: bool):
    kb = []
    if is_joined:
        kb.append([InlineKeyboardButton("Выписаться", callback_data=f"leave:{session_id}")])
    else:
        if can_join:
            kb.append([InlineKeyboardButton("Записаться", callback_data=f"join:{session_id}")])
    kb.append([InlineKeyboardButton("Обновить", callback_data=f"refresh:{session_id}")])
    return InlineKeyboardMarkup(kb)
