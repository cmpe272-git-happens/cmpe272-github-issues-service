"""
SQLite storage for webhook events.

Author: Sukruti Shah
"""


import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "events.db"


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DB_PATH))

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_id TEXT UNIQUE NOT NULL,
            event TEXT NOT NULL,
            action TEXT,
            issue_number INTEGER,
            timestamp TEXT NOT NULL,
            UNIQUE(delivery_id, action)
        )
        """
    )

    connection.commit()
    connection.close()


def save_event(
    delivery_id: str,
    event: str,
    action: Optional[str],
    issue_number: Optional[int],
    timestamp: str,
) -> bool:
    connection = sqlite3.connect(str(DB_PATH))

    try:
        connection.execute(
            """
            INSERT INTO events (
                delivery_id,
                event,
                action,
                issue_number,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                delivery_id,
                event,
                action,
                issue_number,
                timestamp,
            ),
        )

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_events(limit: int = 50):
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            delivery_id,
            event,
            action,
            issue_number,
            timestamp
        FROM events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]
