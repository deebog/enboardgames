import sqlite3
from datetime import datetime

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# Создание таблиц
c.execute("""CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)""")

c.execute("""CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    dt TEXT,
    limit_count INTEGER,
    FOREIGN KEY(game_id) REFERENCES games(id)
)""")

c.execute("""CREATE TABLE IF NOT EXISTS participants (
    session_id INTEGER,
    username TEXT,
    PRIMARY KEY(session_id, username),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
)""")

conn.commit()

# Игры
def add_game(name):
    c.execute("INSERT OR IGNORE INTO games(name) VALUES(?)", (name,))
    conn.commit()

def list_games():
    c.execute("SELECT id,name FROM games ORDER BY name")
    return [{"id": row[0], "name": row[1]} for row in c.fetchall()]

# Сессии
def add_session(game_id, dt_str, limit_count):
    c.execute("INSERT INTO sessions(game_id, dt, limit_count) VALUES(?,?,?)", (game_id, dt_str, limit_count))
    conn.commit()

def list_upcoming_sessions():
    now = datetime.now().isoformat()
    c.execute("""
        SELECT s.id, g.name, s.dt, s.limit_count
        FROM sessions s
        JOIN games g ON s.game_id = g.id
        WHERE s.dt > ?
        ORDER BY s.dt
    """, (now,))
    sessions = []
    for row in c.fetchall():
        session_id, game_name, dt, limit_count = row
        c.execute("SELECT username FROM participants WHERE session_id=?", (session_id,))
        participants = [r[0] for r in c.fetchall()]
        sessions.append({
            "id": session_id,
            "game": game_name,
            "dt": dt,
            "limit": limit_count,
            "participants": participants
        })
    return sessions

def get_session(session_id):
    c.execute("SELECT s.id, g.name, s.dt, s.limit_count FROM sessions s JOIN games g ON s.game_id=g.id WHERE s.id=?", (session_id,))
    row = c.fetchone()
    if not row:
        return None
    session_id, game_name, dt, limit_count = row
    c.execute("SELECT username FROM participants WHERE session_id=?", (session_id,))
    participants = [r[0] for r in c.fetchall()]
    return {"id": session_id, "game": game_name, "dt": dt, "limit": limit_count, "participants": participants}

def add_participant(session_id, username):
    c.execute("INSERT OR IGNORE INTO participants(session_id, username) VALUES(?,?)", (session_id, username))
    conn.commit()

def remove_participant(session_id, username):
    c.execute("DELETE FROM participants WHERE session_id=? AND username=?", (session_id, username))
    conn.commit()

def delete_session(session_id):
    c.execute("DELETE FROM participants WHERE session_id=?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
