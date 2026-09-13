from typing import Any, Optional

import httpx

from app.config import settings


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class GitHubRateLimitError(GitHubAPIError):
    def __init__(
        self,
        reset_at: Optional[str] = None,
        retry_after: Optional[str] = None,
    ):
        super().__init__(
            status_code=429,
            message="GitHub API rate limit exceeded",
        )
        self.reset_at = reset_at
        self.retry_after = retry_after


def normalize_etag(etag: str) -> str:
    """Extract the opaque entity tag for RFC 7232/9110 weak comparison.

    Strips leading W/ (case-insensitive), whitespace, and double quotes.
    """
    cleaned = etag.strip()
    if cleaned.startswith(("W/", "w/")):
        cleaned = cleaned[2:].strip()
    return cleaned.strip('"')


def format_if_none_match(header_val: str) -> str:
    """Format If-None-Match header values so GitHub receives valid quoted ETags (RFC 7232).

    Ensures unquoted entity tags (e.g. from PowerShell curl) are properly quoted.
    """
    parts = []
    for item in header_val.split(","):
        cleaned = item.strip()
        if not cleaned:
            continue
        if cleaned == "*":
            parts.append("*")
            continue
        is_weak = cleaned.startswith(("W/", "w/"))
        opaque = normalize_etag(cleaned)
        parts.append(f'W/"{opaque}"' if is_weak else f'"{opaque}"')
    return ", ".join(parts)


def etags_match(client_header: str, server_etag: str) -> bool:
    """Compare If-None-Match header against server ETag using weak comparison

    as required by RFC 7232 Section 3.2 and RFC 9110 Section 8.8.3.2.
    """
    target = normalize_etag(server_etag)
    if not target:
        return False
    for item in client_header.split(","):
        cleaned = item.strip()
        if not cleaned:
            continue
        if cleaned == "*":
            return True
        if normalize_etag(cleaned) == target:
            return True
    return False


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ):
        self.token = token or settings.github_token
        self.owner = owner or settings.github_owner
        self.repo = repo or settings.github_repo

    @property
    def headers(self) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @property
    def issues_url(self) -> str:
        return (
            f"{self.BASE_URL}/repos/"
            f"{self.owner}/{self.repo}/issues"
        )

    # ---------------------------------------------------------
    # GET /issues
    # Supports pagination, filtering, and conditional GET
    # ---------------------------------------------------------
    async def list_issues(
        self,
        state: str = "open",
        labels: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
        if_none_match: Optional[str] = None,
    ):
        params = {
            "state": state,
            "page": page,
            "per_page": per_page,
        }

        if labels:
            params["labels"] = labels

        extra_headers = {}

        # Forward client's ETag to GitHub
        if if_none_match:
            extra_headers["If-None-Match"] = format_if_none_match(if_none_match)

        response = await self._request(
            "GET",
            self.issues_url,
            params=params,
            headers=extra_headers,
        )

        return response

    # ---------------------------------------------------------
    # GET /issues/{issue_number}
    # ---------------------------------------------------------
    async def get_issue(
        self,
        issue_number: int,
    ):
        url = f"{self.issues_url}/{issue_number}"

        response = await self._request(
            "GET",
            url,
        )

        return response.json()

    # ---------------------------------------------------------
    # POST /issues
    # ---------------------------------------------------------
    async def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
    ):
        payload = {
            "title": title,
        }

        if body is not None:
            payload["body"] = body

        response = await self._request(
            "POST",
            self.issues_url,
            json=payload,
        )

        return response.json()

    # ---------------------------------------------------------
    # PATCH /issues/{issue_number}
    # ---------------------------------------------------------
    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ):
        payload = {}

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["body"] = body

        if state is not None:
            payload["state"] = state

        url = f"{self.issues_url}/{issue_number}"

        response = await self._request(
            "PATCH",
            url,
            json=payload,
        )

        return response.json()

    # ---------------------------------------------------------
    # DELETE equivalent
    # GitHub closes the issue instead of deleting it
    # ---------------------------------------------------------
    async def close_issue(
        self,
        issue_number: int,
    ) -> Any:
        return await self.update_issue(
            issue_number=issue_number,
            state="closed",
        )

    # ---------------------------------------------------------
    # GET /issues/{issue_number}/comments
    # ---------------------------------------------------------
    async def list_comments(
        self,
        issue_number: int,
    ):
        url = (
            f"{self.issues_url}/"
            f"{issue_number}/comments"
        )

        response = await self._request(
            "GET",
            url,
        )

        return response.json()

    # ---------------------------------------------------------
    # POST /issues/{issue_number}/comments
    # ---------------------------------------------------------
    async def create_comment(
        self,
        issue_number: int,
        body: str,
    ):
        url = (
            f"{self.issues_url}/"
            f"{issue_number}/comments"
        )

        payload = {
            "body": body,
        }

        response = await self._request(
            "POST",
            url,
            json=payload,
        )

        return response.json()

    # ---------------------------------------------------------
    # Shared GitHub request handler
    # ---------------------------------------------------------
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ):
        # Start with normal GitHub headers
        request_headers = self.headers.copy()

        # Merge any additional headers
        # such as If-None-Match
        extra_headers = kwargs.pop("headers", None)

        if extra_headers:
            request_headers.update(extra_headers)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=request_headers,
                **kwargs,
            )

        # -------------------------------------------------
        # 304 is valid for Conditional GET
        # -------------------------------------------------
        if response.status_code == 304:
            return response

        # -------------------------------------------------
        # GitHub can signal rate limiting with 403 or 429
        # -------------------------------------------------
        if response.status_code in (403, 429):
            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            if (
                response.status_code == 429
                or remaining == "0"
            ):
                reset_at = response.headers.get(
                    "X-RateLimit-Reset"
                )

                retry_after = response.headers.get(
                    "Retry-After"
                )

                raise GitHubRateLimitError(
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

        # -------------------------------------------------
        # Other GitHub API errors
        # -------------------------------------------------
        if response.status_code >= 400:
            try:
                error_data = response.json()

                message = error_data.get(
                    "message",
                    "GitHub API request failed",
                )

            except Exception:
                message = "GitHub API request failed"

            raise GitHubAPIError(
                status_code=response.status_code,
                message=message,
            )

        return response