"""
ETag and Conditional GET Test Suite

Tests ETag and Conditional GET functionality for the GitHub Issues API.

Covers:
* ETag normalization and formatting;
* weak and strong ETag comparison;
* If-None-Match request handling;
* 200 OK and 304 Not Modified responses;
* GitHub rate-limit header forwarding;
* pagination and Link header handling;
* request ID validation.

Author: Navaneeth Puklath
"""

from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi.testclient import TestClient

from app.github_client import etags_match, format_if_none_match, normalize_etag
from app.main import app
from app.routes import issues

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------
def test_normalize_etag():
    assert normalize_etag('W/"abc"') == "abc"
    assert normalize_etag('w/"abc"') == "abc"
    assert normalize_etag('"abc"') == "abc"
    assert normalize_etag("W/abc") == "abc"
    assert normalize_etag("abc") == "abc"
    assert normalize_etag('  W/"abc"  ') == "abc"
    assert normalize_etag("") == ""


def test_format_if_none_match():
    # Properly quotes weak ETags
    assert format_if_none_match("W/abc") == 'W/"abc"'
    # Preserves already quoted weak ETags
    assert format_if_none_match('W/"abc"') == 'W/"abc"'
    # Properly quotes strong/unquoted ETags
    assert format_if_none_match("abc") == '"abc"'
    assert format_if_none_match('"abc"') == '"abc"'
    # Wildcard
    assert format_if_none_match("*") == "*"
    # Comma-separated list
    assert (
        format_if_none_match('W/abc, "def", 123')
        == 'W/"abc", "def", "123"'
    )


def test_etags_match_weak_comparison():
    server_etag = 'W/"09583ff5a6ce64525301ff4c4e6e232c"'
    # Weak tag match
    assert etags_match('W/"09583ff5a6ce64525301ff4c4e6e232c"', server_etag) is True
    # Strong tag match
    assert etags_match('"09583ff5a6ce64525301ff4c4e6e232c"', server_etag) is True
    # PowerShell unquoted weak tag
    assert etags_match("W/09583ff5a6ce64525301ff4c4e6e232c", server_etag) is True
    # Raw unquoted hash
    assert etags_match("09583ff5a6ce64525301ff4c4e6e232c", server_etag) is True
    # Wildcard *
    assert etags_match("*", server_etag) is True
    # Multiple client tags
    assert (
        etags_match('"unrelated", "09583ff5a6ce64525301ff4c4e6e232c"', server_etag)
        is True
    )
    # Non-matching tag
    assert etags_match('"non-matching"', server_etag) is False
    # Empty string
    assert etags_match("", server_etag) is False


# ---------------------------------------------------------------------------
# Route tests for GET /issues
# ---------------------------------------------------------------------------
def test_normal_get_issues_returns_200_and_etag(monkeypatch):
    mock_response = httpx.Response(
        status_code=200,
        headers={
            "ETag": 'W/"test-etag-123"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1600000000",
        },
        json=[{"id": 1, "title": "Test Issue"}],
    )
    monkeypatch.setattr(
        issues.github_client,
        "list_issues",
        AsyncMock(return_value=mock_response),
    )

    response = client.get("/issues")
    assert response.status_code == 200
    assert response.headers.get("ETag") == 'W/"test-etag-123"'
    assert response.headers.get("X-RateLimit-Limit") == "5000"
    assert response.headers.get("X-RateLimit-Remaining") == "4999"
    assert response.headers.get("X-RateLimit-Reset") == "1600000000"
    assert response.headers.get("X-Request-ID") is not None
    assert response.json() == [{"id": 1, "title": "Test Issue"}]


def test_matching_if_none_match_github_returns_304(monkeypatch):
    mock_response = httpx.Response(
        status_code=304,
        headers={
            "ETag": '"test-etag-123"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4998",
            "X-RateLimit-Reset": "1600000000",
        },
    )
    monkeypatch.setattr(
        issues.github_client,
        "list_issues",
        AsyncMock(return_value=mock_response),
    )

    response = client.get(
        "/issues",
        headers={"If-None-Match": 'W/"test-etag-123"'},
    )
    assert response.status_code == 304
    assert response.headers.get("ETag") == '"test-etag-123"'
    assert response.headers.get("X-RateLimit-Limit") == "5000"
    assert response.headers.get("X-RateLimit-Remaining") == "4998"
    assert response.headers.get("X-RateLimit-Reset") == "1600000000"
    assert response.content == b""


def test_matching_if_none_match_fallback_when_github_returns_200(monkeypatch):
    """
    Even if GitHub returns 200 with the same ETag, the service should still
    return 304 Not Modified to the client.
    """
    mock_response = httpx.Response(
        status_code=200,
        headers={
            "ETag": 'W/"test-etag-123"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4997",
            "X-RateLimit-Reset": "1600000000",
        },
        json=[{"id": 1, "title": "Test Issue"}],
    )
    monkeypatch.setattr(
        issues.github_client,
        "list_issues",
        AsyncMock(return_value=mock_response),
    )

    # PowerShell curl unquoted ETag format
    response = client.get(
        "/issues",
        headers={"If-None-Match": "W/test-etag-123"},
    )
    assert response.status_code == 304
    assert response.headers.get("ETag") == 'W/"test-etag-123"'
    assert response.headers.get("X-RateLimit-Limit") == "5000"
    assert response.headers.get("X-RateLimit-Remaining") == "4997"
    assert response.headers.get("X-RateLimit-Reset") == "1600000000"
    assert response.content == b""


def test_non_matching_if_none_match_returns_200(monkeypatch):
    mock_response = httpx.Response(
        status_code=200,
        headers={
            "ETag": 'W/"new-etag-456"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4996",
            "X-RateLimit-Reset": "1600000000",
        },
        json=[{"id": 2, "title": "New Issue"}],
    )
    monkeypatch.setattr(
        issues.github_client,
        "list_issues",
        AsyncMock(return_value=mock_response),
    )

    response = client.get(
        "/issues",
        headers={"If-None-Match": '"old-etag-123"'},
    )
    assert response.status_code == 200
    assert response.headers.get("ETag") == 'W/"new-etag-456"'
    assert response.headers.get("X-RateLimit-Limit") == "5000"
    assert response.headers.get("X-RateLimit-Remaining") == "4996"
    assert response.headers.get("X-RateLimit-Reset") == "1600000000"
    assert response.json() == [{"id": 2, "title": "New Issue"}]


def test_pagination_and_link_headers_still_work(monkeypatch):
    mock_response = httpx.Response(
        status_code=200,
        headers={
            "ETag": 'W/"page-etag"',
            "Link": '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4995",
            "X-RateLimit-Reset": "1600000000",
        },
        json=[{"id": 3, "title": "Page 1 Issue"}],
    )
    mock_list = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(issues.github_client, "list_issues", mock_list)

    response = client.get("/issues?page=1&per_page=10&state=open")
    assert response.status_code == 200
    assert response.headers.get("Link") == '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next"'
    assert response.headers.get("ETag") == 'W/"page-etag"'
    assert response.headers.get("X-RateLimit-Limit") == "5000"
    assert response.headers.get("X-RateLimit-Remaining") == "4995"
    assert response.headers.get("X-RateLimit-Reset") == "1600000000"

    # Verify query parameters passed through to GitHub client
    mock_list.assert_called_once_with(
        state="open",
        labels=None,
        page=1,
        per_page=10,
        if_none_match=None,
    )

