import httpx
import pytest

from app.github_client import GitHubAPIError, GitHubRateLimitError
from app.routes import issues as issues_routes


def make_github_response(data, headers=None):
    return httpx.Response(
        200,
        json=data,
        headers=headers or {},
        request=httpx.Request(
            "GET",
            "https://api.github.com",
        ),
    )


def patch_async_return(monkeypatch, method_name, value):
    async def fake_method(*args, **kwargs):
        return value

    monkeypatch.setattr(
        issues_routes.github_client,
        method_name,
        fake_method,
    )


def patch_async_error(monkeypatch, method_name, error):
    async def fake_method(*args, **kwargs):
        raise error

    monkeypatch.setattr(
        issues_routes.github_client,
        method_name,
        fake_method,
    )


def test_list_issues_success_and_headers(client, monkeypatch):
    github_response = make_github_response(
        [{"number": 1, "title": "Test issue"}],
        headers={
            "Link": '<https://api.github.com/page=2>; rel="next"',
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "12345",
        },
    )

    patch_async_return(
        monkeypatch,
        "list_issues",
        github_response,
    )

    response = client.get(
        "/issues?state=all&labels=bug&page=2&per_page=10"
    )

    assert response.status_code == 200
    assert response.json()[0]["number"] == 1
    assert "rel=\"next\"" in response.headers["Link"]
    assert response.headers["X-RateLimit-Remaining"] == "4999"


def test_create_issue_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "create_issue",
        {
            "number": 10,
            "title": "New issue",
            "state": "open",
        },
    )

    response = client.post(
        "/issues",
        json={
            "title": "New issue",
            "body": "Issue body",
        },
    )

    assert response.status_code == 201
    assert response.json()["number"] == 10


def test_get_issue_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "get_issue",
        {
            "number": 7,
            "title": "Existing issue",
            "state": "open",
        },
    )

    response = client.get("/issues/7")

    assert response.status_code == 200
    assert response.json()["number"] == 7


def test_update_issue_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "update_issue",
        {
            "number": 7,
            "title": "Updated issue",
            "state": "closed",
        },
    )

    response = client.patch(
        "/issues/7",
        json={
            "title": "Updated issue",
            "state": "closed",
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == "closed"


def test_close_issue_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "close_issue",
        {
            "number": 7,
            "state": "closed",
        },
    )

    response = client.delete("/issues/7")

    assert response.status_code == 200
    assert response.json()["state"] == "closed"


def test_list_comments_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "list_comments",
        [
            {
                "id": 1,
                "body": "Test comment",
            }
        ],
    )

    response = client.get("/issues/7/comments")

    assert response.status_code == 200
    assert response.json()[0]["id"] == 1


def test_create_comment_success(client, monkeypatch):
    patch_async_return(
        monkeypatch,
        "create_comment",
        {
            "id": 2,
            "body": "New comment",
        },
    )

    response = client.post(
        "/issues/7/comments",
        json={"body": "New comment"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == 2


def request_list(client):
    return client.get("/issues")


def request_create(client):
    return client.post(
        "/issues",
        json={"title": "Test issue"},
    )


def request_get(client):
    return client.get("/issues/1")


def request_update(client):
    return client.patch(
        "/issues/1",
        json={"title": "Updated"},
    )


def request_close(client):
    return client.delete("/issues/1")


def request_list_comments(client):
    return client.get("/issues/1/comments")


def request_create_comment(client):
    return client.post(
        "/issues/1/comments",
        json={"body": "Test comment"},
    )


API_ROUTE_CASES = [
    pytest.param(
        "list_issues",
        request_list,
        id="list-issues",
    ),
    pytest.param(
        "create_issue",
        request_create,
        id="create-issue",
    ),
    pytest.param(
        "get_issue",
        request_get,
        id="get-issue",
    ),
    pytest.param(
        "update_issue",
        request_update,
        id="update-issue",
    ),
    pytest.param(
        "close_issue",
        request_close,
        id="close-issue",
    ),
    pytest.param(
        "list_comments",
        request_list_comments,
        id="list-comments",
    ),
    pytest.param(
        "create_comment",
        request_create_comment,
        id="create-comment",
    ),
]


@pytest.mark.parametrize(
    ("method_name", "request_factory"),
    API_ROUTE_CASES,
)
def test_routes_map_github_api_errors(
    client,
    monkeypatch,
    method_name,
    request_factory,
):
    patch_async_error(
        monkeypatch,
        method_name,
        GitHubAPIError(
            status_code=404,
            message="Issue not found",
        ),
    )

    response = request_factory(client)

    assert response.status_code == 404
    assert response.json()["detail"] == "Issue not found"


@pytest.mark.parametrize(
    ("method_name", "request_factory"),
    API_ROUTE_CASES,
)
def test_routes_map_rate_limit_errors(
    client,
    monkeypatch,
    method_name,
    request_factory,
):
    patch_async_error(
        monkeypatch,
        method_name,
        GitHubRateLimitError(
            reset_at="12345",
            retry_after="60",
        ),
    )

    response = request_factory(client)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.headers["X-RateLimit-Reset"] == "12345"