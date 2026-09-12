"""Tests for GitHub webhook validation and event handling.

The tests cover:

* valid and invalid HMAC SHA-256 signatures;
* rejection of tampered request bodies;
* unsupported events and missing actions;
* ``issues``, ``issue_comment``, and ``ping`` events; and
* duplicate deliveries, which should still receive a successful response.

The module creates a small FastAPI application containing only the webhook
router. This keeps the tests isolated from application startup and database
initialization performed by ``app.main``.

Run these tests from the project root with::

    python -m pytest tests/test_webhooks.py -q

Author: Sukruti Shah
"""

import hashlib
import hmac

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.webhook import router


TEST_SECRET = "test-secret"


# Create a small FastAPI app only for webhook tests.
# This avoids importing app.main and therefore avoids init_db().
test_app = FastAPI()
test_app.include_router(router)

client = TestClient(test_app)


def make_signature(body: bytes) -> str:
    """
    Generate the same HMAC SHA-256 signature GitHub would generate.
    """
    return "sha256=" + hmac.new(
        TEST_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()


def test_valid_signature(monkeypatch):
    """
    Valid GitHub signature should be accepted.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    # Pretend SQLite successfully saved the event.
    monkeypatch.setattr(
        "app.routes.webhook.save_event",
        lambda **kwargs: True,
    )

    body = b'{"action":"opened","issue":{"number":1}}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-001",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 204


def test_invalid_signature(monkeypatch):
    """
    Invalid signature should return 401.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    response = client.post(
        "/webhook",
        content=b'{"action":"opened","issue":{"number":1}}',
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-002",
            "X-Hub-Signature-256": "sha256=wrong",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401


def test_tampered_body(monkeypatch):
    """
    If the body changes after GitHub signs it,
    signature validation should fail.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    original_body = b'{"action":"opened","issue":{"number":1}}'
    signature = make_signature(original_body)

    tampered_body = b'{"action":"closed","issue":{"number":1}}'

    response = client.post(
        "/webhook",
        content=tampered_body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-003",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401


def test_unknown_event(monkeypatch):
    """
    Unsupported GitHub event should return 400.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    body = b'{"action":"created"}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "delivery-004",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400


def test_missing_action(monkeypatch):
    """
    Issues event without an action should return 400.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    body = b'{"issue":{"number":1}}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-005",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400


def test_issue_comment(monkeypatch):
    """
    issue_comment event should be accepted.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    saved_event = {}

    def fake_save_event(**kwargs):
        saved_event.update(kwargs)
        return True

    monkeypatch.setattr(
        "app.routes.webhook.save_event",
        fake_save_event,
    )

    body = b'{"action":"created","issue":{"number":10}}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issue_comment",
            "X-GitHub-Delivery": "delivery-006",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 204

    assert saved_event["event"] == "issue_comment"
    assert saved_event["action"] == "created"
    assert saved_event["issue_number"] == 10


def test_ping(monkeypatch):
    """
    Ping should be accepted and passed to save_event.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    saved_event = {}

    def fake_save_event(**kwargs):
        saved_event.update(kwargs)
        return True

    monkeypatch.setattr(
        "app.routes.webhook.save_event",
        fake_save_event,
    )

    body = b'{"zen":"Keep it logically awesome."}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "delivery-ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 204

    assert saved_event["event"] == "ping"
    assert saved_event["action"] == "ping"
    assert saved_event["issue_number"] is None


def test_duplicate_retry_returns_success(monkeypatch):
    """
    Simulate database saying the webhook is a duplicate.

    The webhook should still acknowledge GitHub with 204.
    """

    monkeypatch.setenv("WEBHOOK_SECRET", TEST_SECRET)

    # False means save_event detected a duplicate.
    monkeypatch.setattr(
        "app.routes.webhook.save_event",
        lambda **kwargs: False,
    )

    body = b'{"action":"opened","issue":{"number":20}}'
    signature = make_signature(body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "duplicate-delivery",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 204
