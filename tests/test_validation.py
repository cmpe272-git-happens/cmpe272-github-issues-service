"""
Tests for API request validation.

These tests verify that invalid requests are rejected correctly,
including missing issue titles, empty titles, and unsupported issue states.

The application converts FastAPI validation errors into HTTP 400
responses as required by the service contract.

Author: Juilee Giramkar
"""
def test_create_issue_without_title_returns_400(client):
    response = client.post(
        "/issues",
        json={"body": "This request has no title."},
    )

    assert response.status_code == 400


def test_create_issue_with_empty_title_returns_400(client):
    response = client.post(
        "/issues",
        json={"title": ""},
    )

    assert response.status_code == 400


def test_update_issue_with_invalid_state_returns_400(client):
    response = client.patch(
        "/issues/1",
        json={"state": "invalid"},
    )

    assert response.status_code == 400
