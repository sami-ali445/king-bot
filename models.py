"""
King Bot - Database Models
SQLite Database with all tables
"""

import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            points INTEGER DEFAULT 0,
            balance REAL DEFAULT 0.0,
            referrer_id INTEGER DEFAULT NULL,
            joined_at TEXT DEFAULT (datetime('now')),
            is_banned INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS virtual_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id TEXT,
            phone_number TEXT,
            country_code TEXT,
            country_name TEXT,
            service TEXT DEFAULT 'any',
            price REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            sms_code TEXT,
            sms_text TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            target TEXT,
            points_reward INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS boosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            boost_type TEXT NOT NULL,
            target TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            points_cost INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_type TEXT NOT NULL,
            amount REAL DEFAULT 0,
            description TEXT,
            status TEXT DEFAULT 'pending',
            tx_hash TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            approved_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            message TEXT,
            sent_at TEXT DEFAULT (datetime('now')),
            recipients_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);
        CREATE INDEX IF NOT EXISTS idx_numbers_user ON virtual_numbers(user_id);
        CREATE INDEX IF NOT EXISTS idx_numbers_status ON virtual_numbers(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_boosts_user ON boosts(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    """)

    # Clean old branding from settings table
    conn.execute("DELETE FROM settings WHERE value LIKE '%جولدن%' OR value LIKE '%Golden%' OR value LIKE '%golden%' OR value LIKE '%Grid%'")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bot_name', 'كينغ بوت �')")
    conn.commit()
    conn.close()
    print("[DB] Initialized OK")


if __name__ == "__main__":
    init_db()
