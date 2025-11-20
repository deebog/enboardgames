import sqlite3
from bot.config import DB_PATH

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        game_id INTEGER NOT NULL,
        limit_players INTEGER NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS registrations (
        session_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY (session_id, user_id)
    )""")
    conn.commit()
    conn.close()
