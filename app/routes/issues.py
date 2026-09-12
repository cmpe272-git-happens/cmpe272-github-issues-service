from fastapi import APIRouter, HTTPException, Query

from app.github_client import GitHubAPIError, GitHubClient, GitHubRateLimitError
from app.schemas import CommentCreate, IssueCreate, IssueUpdate


router = APIRouter(prefix="/issues", tags=["Issues"])

github_client = GitHubClient()


@router.get("")
async def list_issues(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    try:
        return await github_client.list_issues(
            page=page,
            per_page=per_page,
        )
    except GitHubRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.post("", status_code=201)
async def create_issue(issue: IssueCreate):
    try:
        return await github_client.create_issue(
            title=issue.title,
            body=issue.body,
        )
    except GitHubRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.get("/{issue_number}")
async def get_issue(issue_number: int):
    try:
        return await github_client.get_issue(issue_number)
    except GitHubRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


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
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.delete("/{issue_number}")
async def close_issue(issue_number: int):
    try:
        return await github_client.close_issue(issue_number)
    except GitHubRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.get("/{issue_number}/comments")
async def list_comments(issue_number: int):
    try:
        return await github_client.list_comments(issue_number)
    except GitHubRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


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
        raise HTTPException(
            status_code=429,
            detail=exc.message,
        )
    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
