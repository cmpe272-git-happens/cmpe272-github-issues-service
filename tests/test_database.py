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


def test_ping_event_allows_missing_issue_number(temporary_database):
    """Ping events persist successfully without an issue number."""
    assert database.save_event(
        delivery_id="delivery-ping",
        event="ping",
        action="ping",
        issue_number=None,
        timestamp="2026-09-12T00:00:00+00:00",
    ) is True

    assert database.get_events()[0]["issue_number"] is None


def test_get_events_respects_limit(temporary_database):
    """get_events returns no more than the requested number of rows."""
    for index in range(3):
        assert database.save_event(
            delivery_id=f"delivery-limit-{index}",
            event="issues",
            action="opened",
            issue_number=index + 1,
            timestamp=f"2026-09-12T00:0{index}:00+00:00",
        ) is True

    assert len(database.get_events(limit=2)) == 2


def test_get_events_returns_newest_events_first(temporary_database):
    """get_events orders rows from newest insertion to oldest insertion."""
    for index in range(3):
        assert database.save_event(
            delivery_id=f"delivery-order-{index}",
            event="issues",
            action="opened",
            issue_number=index + 1,
            timestamp=f"2026-09-12T00:0{index}:00+00:00",
        ) is True

    events = database.get_events()

    assert [event["id"] for event in events] == [
        "delivery-order-2",
        "delivery-order-1",
        "delivery-order-0",
    ]


def test_empty_database_returns_empty_list(temporary_database):
    """An initialized database with no events returns an empty list."""
    assert database.get_events() == []


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
