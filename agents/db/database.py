"""SQLite database for sessions and X OAuth tokens."""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./vibelauncher.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS launch_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            status TEXT DEFAULT 'pending',
            state_json TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS x_tokens (
            user_id TEXT PRIMARY KEY,
            screen_name TEXT,
            access_token TEXT,
            access_token_secret TEXT,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()


def create_session(launch_id: str, user_id: str, initial_state: dict) -> None:
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO launch_sessions (id, user_id, status, state_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (launch_id, user_id, "pending", json.dumps(initial_state), now, now),
    )
    conn.commit()
    conn.close()


def update_session(launch_id: str, status: str, state: dict) -> None:
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE launch_sessions SET status=?, state_json=?, updated_at=? WHERE id=?",
        (status, json.dumps(state), now, launch_id),
    )
    conn.commit()
    conn.close()


def get_session(launch_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM launch_sessions WHERE id=?", (launch_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "status": row["status"],
        "state": json.loads(row["state_json"]),
        "created_at": row["created_at"],
    }


def save_x_tokens(user_id: str, screen_name: str, access_token: str, access_token_secret: str) -> None:
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO x_tokens (user_id, screen_name, access_token, access_token_secret, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, screen_name, access_token, access_token_secret, now),
    )
    conn.commit()
    conn.close()


def get_x_tokens(user_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM x_tokens WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "screen_name": row["screen_name"],
        "access_token": row["access_token"],
        "access_token_secret": row["access_token_secret"],
    }
