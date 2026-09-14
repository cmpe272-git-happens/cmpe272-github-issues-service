# Navaneeth 
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubRateLimitError,
    etags_match,
)
from app.schemas import CommentCreate, IssueCreate, IssueUpdate


router = APIRouter(prefix="/issues", tags=["Issues"])

github_client = GitHubClient()


# ---------------------------------------------------------
# GET /issues
# List issues with pagination, filtering, Link headers,
# rate-limit headers, and ETag / Conditional GET support
# ---------------------------------------------------------
@router.get("")
async def list_issues(
    request: Request,
    response: Response,
    state: Literal["open", "closed", "all"] = Query("open"),
    labels: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    try:
        # Read If-None-Match sent by the client
        if_none_match = request.headers.get("If-None-Match")

        # Forward conditional GET header to GitHub
        github_response = await github_client.list_issues(
            state=state,
            labels=labels,
            page=page,
            per_page=per_page,
            if_none_match=if_none_match,
        )

        # Get ETag returned by GitHub
        etag = github_response.headers.get("ETag")

        # Collect GitHub rate-limit information to include in responses
        rate_limit_headers = {}
        for header_name in (
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ):
            val = github_response.headers.get(header_name)
            if val:
                rate_limit_headers[header_name] = val

        # -------------------------------------------------
        # Conditional GET / 304 Not Modified
        # -------------------------------------------------

        # Case 1:
        # GitHub directly returned 304
        if github_response.status_code == 304:
            headers = {**rate_limit_headers}

            if etag:
                headers["ETag"] = etag
            elif if_none_match:
                headers["ETag"] = if_none_match

            return Response(
                status_code=304,
                headers=headers,
            )

        # Case 2:
        # GitHub returned 200, but the ETag still matches
        # one of the values sent by the client (weak comparison per RFC 7232 / RFC 9110).
        if if_none_match and etag and etags_match(if_none_match, etag):
            headers = {
                **rate_limit_headers,
                "ETag": etag,
            }
            return Response(
                status_code=304,
                headers=headers,
            )

        # -------------------------------------------------
        # Forward GitHub ETag header on normal 200 response
        # -------------------------------------------------
        if etag:
            response.headers["ETag"] = etag

        # -------------------------------------------------
        # Forward GitHub pagination Link header
        # -------------------------------------------------
        link_header = github_response.headers.get("Link")

        if link_header:
            response.headers["Link"] = link_header

        # -------------------------------------------------
        # Forward useful GitHub rate-limit information
        # -------------------------------------------------
        for header_name, header_val in rate_limit_headers.items():
            response.headers[header_name] = header_val

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
