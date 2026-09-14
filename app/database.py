"""
SQLite persistence layer for GitHub webhook events.

This module is responsible for:
- creating and initializing the local events database;
- opening SQLite connections with bounded lock timeouts;
- retrying short-lived database lock errors;
- persisting webhook events safely;
- rejecting duplicate webhook deliveries;
- surfacing unexpected database integrity errors; and
- returning the most recent processed events for the /events endpoint.

Webhook events are stored in data/events.db by default. The database path can
be mounted to persistent storage when the application runs inside Docker.

Author: Sukruti Shah
"""


import sqlite3
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "events.db"
SQLITE_TIMEOUT_SECONDS = 1.0
SQLITE_BUSY_TIMEOUT_MS = 1000
WRITE_RETRIES = 2


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection with a short, bounded lock wait."""
    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=SQLITE_TIMEOUT_SECONDS,
    )
    connection.execute(
        f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}"
    )
    return connection


def _is_locked_error(error: sqlite3.OperationalError) -> bool:
    """Return whether SQLite rejected the operation because it was locked."""
    return "locked" in str(error).lower()


def init_db():
    """Create the data directory and events table if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _connect() as connection:
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


def save_event(
    delivery_id: str,
    event: str,
    action: Optional[str],
    issue_number: Optional[int],
    timestamp: str,
) -> bool:
    """Persist one webhook event and return False for a duplicate delivery."""
    for attempt in range(WRITE_RETRIES + 1):
        try:
            with _connect() as connection:
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
            return True

        except sqlite3.IntegrityError as error:
            # Keep duplicate delivery behavior, but do not hide other errors.
            if "UNIQUE constraint failed" in str(error):
                return False
            raise

        except sqlite3.OperationalError as error:
            if not _is_locked_error(error) or attempt >= WRITE_RETRIES:
                raise
            time.sleep(0.05 * (attempt + 1))

    return False


def get_events(limit: int = 50):
    """Return the newest persisted webhook events for the events endpoint."""
    with _connect() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                delivery_id AS id,
                event,
                action,
                issue_number,
                timestamp
            FROM events
            ORDER BY events.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]
