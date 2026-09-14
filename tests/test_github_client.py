"""
Mocked unit tests for the GitHub API client.

These tests verify request headers, URL construction, issue CRUD
operations, comment operations, GitHub API error handling, and
rate-limit behavior.

External GitHub requests are mocked so the tests run safely without
depending on the live GitHub API.

Author: Juilee Giramkar
"""
import asyncio

import httpx
import pytest

from app import github_client as github_client_module
from app.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubRateLimitError,
)


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def request(self, method, url, **kwargs):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "kwargs": kwargs,
            }
        )
        return self.response


def make_response(status_code, json_data=None, headers=None, text=None):
    request = httpx.Request("GET", "https://api.github.com")

    if json_data is not None:
        return httpx.Response(
            status_code,
            json=json_data,
            headers=headers or {},
            request=request,
        )

    return httpx.Response(
        status_code,
        text=text or "",
        headers=headers or {},
        request=request,
    )


def install_fake_client(monkeypatch, response):
    fake_client = FakeAsyncClient(response)

    monkeypatch.setattr(
        github_client_module.httpx,
        "AsyncClient",
        lambda: fake_client,
    )

    return fake_client


def test_headers_and_url():
    client = GitHubClient(
        token="test-token",
        owner="test-owner",
        repo="test-repo",
    )

    assert client.headers["Accept"] == "application/vnd.github+json"
    assert client.headers["Authorization"] == "Bearer test-token"
    assert client.issues_url.endswith(
        "/repos/test-owner/test-repo/issues"
    )


def test_list_issues_sends_parameters(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(200, [{"number": 1}]),
    )

    client = GitHubClient("token", "owner", "repo")

    result = asyncio.run(
        client.list_issues(
            state="all",
            labels="bug",
            page=2,
            per_page=50,
        )
    )

    assert result.json() == [{"number": 1}]
    assert fake.calls[0]["kwargs"]["params"] == {
        "state": "all",
        "page": 2,
        "per_page": 50,
        "labels": "bug",
    }


def test_list_issues_without_labels(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(200, []),
    )

    client = GitHubClient("token", "owner", "repo")

    asyncio.run(client.list_issues(labels=None))

    assert "labels" not in fake.calls[0]["kwargs"]["params"]


def test_get_issue(monkeypatch):
    install_fake_client(
        monkeypatch,
        make_response(200, {"number": 7, "title": "Test issue"}),
    )

    client = GitHubClient("token", "owner", "repo")
    result = asyncio.run(client.get_issue(7))

    assert result["number"] == 7
    assert result["title"] == "Test issue"


def test_create_issue_with_body(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(201, {"number": 2}),
    )

    client = GitHubClient("token", "owner", "repo")

    asyncio.run(
        client.create_issue(
            title="New issue",
            body="Issue details",
        )
    )

    assert fake.calls[0]["kwargs"]["json"] == {
        "title": "New issue",
        "body": "Issue details",
    }


def test_create_issue_without_body(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(201, {"number": 3}),
    )

    client = GitHubClient("token", "owner", "repo")

    asyncio.run(client.create_issue(title="New issue"))

    assert fake.calls[0]["kwargs"]["json"] == {
        "title": "New issue",
    }


def test_update_issue(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(200, {"number": 4, "state": "closed"}),
    )

    client = GitHubClient("token", "owner", "repo")

    result = asyncio.run(
        client.update_issue(
            issue_number=4,
            title="Updated",
            body="Updated body",
            state="closed",
        )
    )

    assert result["state"] == "closed"
    assert fake.calls[0]["kwargs"]["json"] == {
        "title": "Updated",
        "body": "Updated body",
        "state": "closed",
    }


def test_close_issue(monkeypatch):
    client = GitHubClient("token", "owner", "repo")
    captured = {}

    async def fake_update_issue(**kwargs):
        captured.update(kwargs)
        return {"state": "closed"}

    monkeypatch.setattr(
        client,
        "update_issue",
        fake_update_issue,
    )

    result = asyncio.run(client.close_issue(9))

    assert result["state"] == "closed"
    assert captured == {
        "issue_number": 9,
        "state": "closed",
    }


def test_list_comments(monkeypatch):
    install_fake_client(
        monkeypatch,
        make_response(200, [{"id": 1, "body": "Comment"}]),
    )

    client = GitHubClient("token", "owner", "repo")
    result = asyncio.run(client.list_comments(5))

    assert result[0]["body"] == "Comment"


def test_create_comment(monkeypatch):
    fake = install_fake_client(
        monkeypatch,
        make_response(201, {"id": 10, "body": "New comment"}),
    )

    client = GitHubClient("token", "owner", "repo")
    result = asyncio.run(client.create_comment(5, "New comment"))

    assert result["id"] == 10
    assert fake.calls[0]["kwargs"]["json"] == {
        "body": "New comment",
    }


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (401, "Bad credentials"),
        (404, "Issue not found"),
        (500, "GitHub server error"),
    ],
)
def test_api_error_mapping(monkeypatch, status_code, message):
    install_fake_client(
        monkeypatch,
        make_response(status_code, {"message": message}),
    )

    client = GitHubClient("token", "owner", "repo")

    with pytest.raises(GitHubAPIError) as error:
        asyncio.run(client.get_issue(1))

    assert error.value.status_code == status_code
    assert error.value.message == message


def test_rate_limit_429(monkeypatch):
    install_fake_client(
        monkeypatch,
        make_response(
            429,
            headers={
                "X-RateLimit-Reset": "12345",
                "Retry-After": "60",
            },
        ),
    )

    client = GitHubClient("token", "owner", "repo")

    with pytest.raises(GitHubRateLimitError) as error:
        asyncio.run(client.get_issue(1))

    assert error.value.status_code == 429
    assert error.value.reset_at == "12345"
    assert error.value.retry_after == "60"


def test_rate_limit_403_with_zero_remaining(monkeypatch):
    install_fake_client(
        monkeypatch,
        make_response(
            403,
            headers={"X-RateLimit-Remaining": "0"},
        ),
    )

    client = GitHubClient("token", "owner", "repo")

    with pytest.raises(GitHubRateLimitError):
        asyncio.run(client.get_issue(1))
