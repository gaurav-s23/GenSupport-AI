import os
import sqlite3
from datetime import datetime

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "support.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # so we can use dict-like access
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Main ticket table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        intent TEXT,
        sentiment TEXT,
        agent_action TEXT,
        created_at TEXT
    )
    """)

    # Messages table (per ticket)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        sender TEXT,      
        message TEXT,
        timestamp TEXT,
        FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
    )
    """)

    conn.commit()
    conn.close()
    print("[DB] Initialized successfully!")


def create_ticket(user_id, intent, sentiment, action):
    conn = get_connection()
    cursor = conn.cursor()

    ts = datetime.utcnow().isoformat()
    cursor.execute(
        """
        INSERT INTO tickets (user_id, intent, sentiment, agent_action, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, intent, sentiment, action, ts),
    )

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def add_message(ticket_id, sender, message):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO messages (ticket_id, sender, message, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (ticket_id, sender, message, ts),
    )

    conn.commit()
    conn.close()


def get_all_tickets():
    """
    Returns list of dicts: all tickets ordered by newest first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ticket_id, user_id, intent, sentiment, agent_action, created_at
        FROM tickets
        ORDER BY created_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_messages(ticket_id: int):
    """
    Returns list of dicts: all messages for one ticket.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT msg_id, sender, message, timestamp
        FROM messages
        WHERE ticket_id = ?
        ORDER BY timestamp ASC
        """,
        (ticket_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
