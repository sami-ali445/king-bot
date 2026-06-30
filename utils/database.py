"""
King Bot - Database Operations
Direct DB calls - no HTTP self-calls
"""

import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ========== Users ==========
def register_user(user_id: int, username: str, full_name: str) -> bool:
    conn = get_db()
    existing = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not existing:
        clean_name = full_name
        for bad in ["جولدن جريد", "جولدن", "جريد", "Golden Grid", "Golden", "golden"]:
            clean_name = clean_name.replace(bad, "—")
        username = username or "—"
        conn.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, strip_non_arabic(clean_name) if False else clean_name.strip() or "—", )
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_count() -> int:
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    conn.close()
    return row["cnt"]


def ban_user(user_id: int, banned: bool = True):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))
    conn.commit()
    conn.close()


# ========== Points & Balance ==========
def add_points(user_id: int, points: int):
    conn = get_db()
    conn.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()


def deduct_points(user_id: int, points: int) -> bool:
    conn = get_db()
    row = conn.execute("SELECT points FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not row or row["points"] < points:
        conn.close()
        return False
    conn.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()
    return True


def get_points(user_id: int) -> int:
    conn = get_db()
    row = conn.execute("SELECT points FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["points"] if row else 0


def add_balance(user_id: int, amount: float):
    conn = get_db()
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> float:
    conn = get_db()
    row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["balance"] if row else 0.0


# ========== Virtual Numbers ==========
def save_number(user_id: int, order_id: str, phone: str, country_code: str, country_name: str, price: float) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO virtual_numbers (user_id, order_id, phone_number, country_code, country_name, price, status) "
        "VALUES (?, ?, ?, ?, ?, ?, 'active')",
        (user_id, order_id, phone, country_code, country_name, price)
    )
    conn.commit()
    number_id = cur.lastrowid
    conn.close()
    return number_id


def update_number_sms(number_id: int, sms_code: str, sms_text: str):
    conn = get_db()
    conn.execute(
        "UPDATE virtual_numbers SET sms_code = ?, sms_text = ? WHERE id = ?",
        (sms_code, sms_text, number_id)
    )
    conn.commit()
    conn.close()


def cancel_number(number_id: int):
    conn = get_db()
    conn.execute("UPDATE virtual_numbers SET status = 'cancelled' WHERE id = ?", (number_id,))
    conn.commit()
    conn.close()


def get_user_numbers(user_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM virtual_numbers WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_number_by_order(order_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM virtual_numbers WHERE order_id = ? AND status = 'active'", (order_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ========== Tasks (Earn Points) ==========
def create_task(user_id: int, task_type: str, target: str, points_reward: int) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO tasks (user_id, task_type, target, points_reward, status) VALUES (?, ?, ?, ?, 'pending')",
        (user_id, task_type, target, points_reward)
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def complete_task(task_id: int) -> dict:
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return {"success": False, "error": "المهمة غير موجودة"}
    if task["status"] == "completed":
        conn.close()
        return {"success": False, "error": "مكتملة بالفعل"}

    conn.execute("UPDATE tasks SET status = 'completed', completed_at = datetime('now') WHERE id = ?", (task_id,))
    conn.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (task["points_reward"], task["user_id"]))
    conn.commit()
    conn.close()
    return {"success": True, "points": task["points_reward"], "user_id": task["user_id"]}


def get_pending_tasks() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ========== Boosts (Spend Points) ==========
def create_boost(user_id: int, boost_type: str, target: str, quantity: int, points_cost: int) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO boosts (user_id, boost_type, target, quantity, points_cost, status) "
        "VALUES (?, ?, ?, ?, ?, 'pending')",
        (user_id, boost_type, target, quantity, points_cost)
    )
    conn.commit()
    boost_id = cur.lastrowid
    conn.close()
    return boost_id


def get_pending_boosts() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM boosts WHERE status = 'pending' ORDER BY created_at ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_boost(boost_id: int):
    conn = get_db()
    conn.execute("UPDATE boosts SET status = 'completed' WHERE id = ?", (boost_id,))
    conn.commit()
    conn.close()


# ========== Orders (Deposits) ==========
def create_order(user_id: int, order_type: str, amount: float, description: str = "") -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO orders (user_id, order_type, amount, description) VALUES (?, ?, ?, ?)",
        (user_id, order_type, amount, description)
    )
    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return order_id


def approve_order(order_id: int) -> dict:
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return {"success": False, "error": "الطلب غير موجود"}
    if order["status"] == "completed":
        conn.close()
        return {"success": False, "error": "مكتمل بالفعل"}

    conn.execute("UPDATE orders SET status = 'completed', approved_at = datetime('now') WHERE id = ?", (order_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (order["amount"], order["user_id"]))
    conn.commit()
    conn.close()
    return {"success": True, "amount": order["amount"], "user_id": order["user_id"]}


def get_pending_orders() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id = u.user_id "
        "WHERE o.status = 'pending' ORDER BY o.created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_orders(limit: int = 50) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id = u.user_id "
        "ORDER BY o.created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ========== Broadcasts ==========
def save_broadcast(admin_id: int, message: str, recipients_count: int) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO broadcasts (admin_id, message, recipients_count) VALUES (?, ?, ?)",
        (admin_id, message, recipients_count)
    )
    conn.commit()
    broadcast_id = cur.lastrowid
    conn.close()
    return broadcast_id


# ========== Stats ==========
def get_stats() -> dict:
    conn = get_db()
    users_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    active_numbers = conn.execute("SELECT COUNT(*) as cnt FROM virtual_numbers WHERE status = 'active'").fetchone()["cnt"]
    pending_tasks = conn.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'pending'").fetchone()["cnt"]
    pending_boosts = conn.execute("SELECT COUNT(*) as cnt FROM boosts WHERE status = 'pending'").fetchone()["cnt"]
    pending_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'pending'").fetchone()["cnt"]
    total_deposits = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM orders WHERE status = 'completed'").fetchone()["total"]
    conn.close()
    return {
        "users": users_count,
        "active_numbers": active_numbers,
        "pending_tasks": pending_tasks,
        "pending_boosts": pending_boosts,
        "pending_orders": pending_orders,
        "total_deposits": total_deposits
    }
