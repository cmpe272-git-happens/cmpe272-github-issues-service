import sqlite3

import pytest

from app import database


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    """Use an isolated SQLite file for each persistence test."""
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "events.db")
    database.init_db()
    return database.DB_PATH


def test_init_db_creates_events_table(temporary_database):
    """Database initialization creates the events table on disk."""
    with sqlite3.connect(temporary_database) as connection:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'events'
            """
        ).fetchone()

    assert table == ("events",)


def test_save_event_persists_across_connections(temporary_database):
    """A committed event remains available after reopening SQLite."""
    assert database.save_event(
        delivery_id="delivery-001",
        event="issues",
        action="opened",
        issue_number=42,
        timestamp="2026-09-12T00:00:00+00:00",
    ) is True

    events = database.get_events()

    assert events == [
        {
            "id": "delivery-001",
            "event": "issues",
            "action": "opened",
            "issue_number": 42,
            "timestamp": "2026-09-12T00:00:00+00:00",
        }
    ]


def test_duplicate_delivery_is_not_inserted(temporary_database):
    """A repeated delivery is reported as a duplicate and stored once."""
    event = {
        "delivery_id": "delivery-duplicate",
        "event": "issues",
        "action": "opened",
        "issue_number": 42,
        "timestamp": "2026-09-12T00:00:00+00:00",
    }

    assert database.save_event(**event) is True
    assert database.save_event(**event) is False
    assert len(database.get_events()) == 1


def test_non_duplicate_integrity_errors_are_not_hidden(temporary_database):
    """Unexpected integrity failures remain visible to the caller."""
    with pytest.raises(sqlite3.IntegrityError):
        database.save_event(
            delivery_id=None,
            event="issues",
            action="opened",
            issue_number=42,
            timestamp="2026-09-12T00:00:00+00:00",
        )
