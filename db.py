import sqlite3
from config import DB_PATH

def init_db():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS games(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS meetings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        game_id INTEGER,
        limit_count INTEGER
    )""")
    conn.commit()
    conn.close()
