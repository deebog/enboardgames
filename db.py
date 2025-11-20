import sqlite3
import os
from datetime import datetime

DB_FILE = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            dt_utc TEXT,
            limit_participants INTEGER,
            FOREIGN KEY(game_id) REFERENCES games(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            username TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def add_game(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO games(name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def list_games():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM games")
    result = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in result]

def add_session(game_id, dt_utc, limit):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sessions(game_id, dt_utc, limit_participants) VALUES (?, ?, ?)", (game_id, dt_utc, limit))
    conn.commit()
    conn.close()

def list_upcoming_sessions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("""
        SELECT s.id, g.name, s.dt_utc, s.limit_participants
        FROM sessions s
        JOIN games g ON g.id = s.game_id
        WHERE s.dt_utc >= ?
        ORDER BY s.dt_utc ASC
    """, (now,))
    sessions = []
    for row in c.fetchall():
        session_id, game, dt_utc, limit = row
        c.execute("SELECT username FROM participants WHERE session_id = ?", (session_id,))
        participants = [r[0] for r in c.fetchall()]
        sessions.append({
            "id": session_id,
            "game": game,
            "dt_utc": dt_utc,
            "limit": limit,
            "participants": participants
        })
    conn.close()
    return sessions

def get_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT s.id, g.name, s.dt_utc, s.limit_participants
        FROM sessions s
        JOIN games g ON g.id = s.game_id
        WHERE s.id = ?
    """, (session_id,))
    row = c.fetchone()
    if not row:
        return None
    session_id, game, dt_utc, limit = row
    c.execute("SELECT username FROM participants WHERE session_id = ?", (session_id,))
    participants = [r[0] for r in c.fetchall()]
    conn.close()
    return {"id": session_id, "game": game, "dt_utc": dt_utc, "limit": limit, "participants": participants}

def add_participant(session_id, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO participants(session_id, username) VALUES (?, ?)", (session_id, username))
    conn.commit()
    conn.close()

def remove_participant(session_id, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM participants WHERE session_id = ? AND username = ?", (session_id, username))
    conn.commit()
    conn.close()

def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM participants WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
