from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def get_add_game_button():
    return InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("➕ Добавить игру", callback_data="addgame")
    ])

def get_game_selection_buttons(games):
    buttons = [InlineKeyboardButton(g['name'], callback_data=f"selgame_{g['id']}") for g in games]
    return InlineKeyboardMarkup.from_column(buttons)
