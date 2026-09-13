from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from app.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubRateLimitError,
)
from app.schemas import CommentCreate, IssueCreate, IssueUpdate


router = APIRouter(prefix="/issues", tags=["Issues"])

github_client = GitHubClient()


# ---------------------------------------------------------
# GET /issues
# List issues with pagination, filtering, and Link headers
# ---------------------------------------------------------
@router.get("")
async def list_issues(
    response: Response,
    state: Literal["open", "closed", "all"] = Query("open"),
    labels: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    try:
        github_response = await github_client.list_issues(
            state=state,
            labels=labels,
            page=page,
            per_page=per_page,
        )

        # Forward GitHub pagination Link header
        link_header = github_response.headers.get("Link")

        if link_header:
            response.headers["Link"] = link_header

        # Forward useful GitHub rate-limit information
        rate_limit = github_response.headers.get("X-RateLimit-Limit")
        rate_remaining = github_response.headers.get("X-RateLimit-Remaining")
        rate_reset = github_response.headers.get("X-RateLimit-Reset")

        if rate_limit:
            response.headers["X-RateLimit-Limit"] = rate_limit

        if rate_remaining:
            response.headers["X-RateLimit-Remaining"] = rate_remaining

        if rate_reset:
            response.headers["X-RateLimit-Reset"] = rate_reset

        return github_response.json()

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# POST /issues
# Create a new issue
# ---------------------------------------------------------
@router.post("", status_code=201)
async def create_issue(issue: IssueCreate):
    try:
        return await github_client.create_issue(
            title=issue.title,
            body=issue.body,
        )

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# GET /issues/{issue_number}
# Get one GitHub issue
# ---------------------------------------------------------
@router.get("/{issue_number}")
async def get_issue(issue_number: int):
    try:
        return await github_client.get_issue(issue_number)

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# PATCH /issues/{issue_number}
# Update title/body/state
# ---------------------------------------------------------
@router.patch("/{issue_number}")
async def update_issue(
    issue_number: int,
    issue: IssueUpdate,
):
    try:
        return await github_client.update_issue(
            issue_number=issue_number,
            title=issue.title,
            body=issue.body,
            state=issue.state,
        )

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# DELETE /issues/{issue_number}
# GitHub does not actually delete issues.
# This closes the issue instead.
# ---------------------------------------------------------
@router.delete("/{issue_number}")
async def close_issue(issue_number: int):
    try:
        return await github_client.close_issue(issue_number)

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# GET /issues/{issue_number}/comments
# List comments
# ---------------------------------------------------------
@router.get("/{issue_number}/comments")
async def list_comments(issue_number: int):
    try:
        return await github_client.list_comments(issue_number)

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------
# POST /issues/{issue_number}/comments
# Create a comment
# ---------------------------------------------------------
@router.post("/{issue_number}/comments", status_code=201)
async def create_comment(
    issue_number: int,
    comment: CommentCreate,
):
    try:
        return await github_client.create_comment(
            issue_number=issue_number,
            body=comment.body,
        )

    except GitHubRateLimitError as exc:
        headers = {}

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        if exc.reset_at:
            headers["X-RateLimit-Reset"] = str(exc.reset_at)

        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers=headers,
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc