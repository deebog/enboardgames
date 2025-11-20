import sqlite3
from contextlib import closing
from datetime import datetime
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            dt_utc TEXT NOT NULL, -- ISO UTC datetime string
            limit_count INTEGER NOT NULL,
            creator_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS participants (
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (session_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            reminders_enabled INTEGER DEFAULT 1
        );
        """)
        conn.commit()

# Games
def list_games():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM games ORDER BY name")
        return cur.fetchall()

def add_game(name: str):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO games (name) VALUES (?)", (name.strip(),))
            conn.commit()
            return True
        except Exception:
            return False

def delete_game_by_id(game_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM games WHERE id=?", (game_id,))
        conn.commit()

def get_game(game_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM games WHERE id=?", (game_id,))
        return cur.fetchone()

# Sessions
def add_session(game_id: int, dt_utc_iso: str, limit_count: int, creator_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO sessions (game_id, dt_utc, limit_count, creator_id) VALUES (?,?,?,?)",
                    (game_id, dt_utc_iso, limit_count, creator_id))
        conn.commit()
        return cur.lastrowid

def get_session(session_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT s.*, g.name as game_name FROM sessions s JOIN games g ON s.game_id=g.id WHERE s.id=?",
                    (session_id,))
        return cur.fetchone()

def list_upcoming_sessions():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT s.*, g.name as game_name FROM sessions s JOIN games g ON s.game_id=g.id ORDER BY s.dt_utc")
        return cur.fetchall()

def delete_session(session_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM participants WHERE session_id=?", (session_id,))
        cur.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()

# Participants
def add_participant(session_id: int, user_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO participants (session_id, user_id) VALUES (?,?)", (session_id, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_participant(session_id: int, user_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM participants WHERE session_id=? AND user_id=?", (session_id, user_id))
        conn.commit()

def list_participants(session_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM participants WHERE session_id=?", (session_id,))
        return [r["user_id"] for r in cur.fetchall()]

def participant_count(session_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM participants WHERE session_id=?", (session_id,))
        return cur.fetchone()["c"]

# Users reminders
def set_user_reminders(user_id: int, enabled: bool):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id, reminders_enabled) VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET reminders_enabled=excluded.reminders_enabled",
                    (user_id, 1 if enabled else 0))
        conn.commit()

def get_user_reminders(user_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT reminders_enabled FROM users WHERE user_id=?", (user_id,))
        r = cur.fetchone()
        return bool(r["reminders_enabled"]) if r else True
