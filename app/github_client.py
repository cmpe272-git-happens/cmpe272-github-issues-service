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

    async def list_issues(
        self,
        state: str = "open",
        labels: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
    ):
        params = {
            "state": state,
            "page": page,
            "per_page": per_page,
        }

        if labels:
            params["labels"] = labels

        response = await self._request(
            "GET",
            self.issues_url,
            params=params,
        )

        return response

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

    async def close_issue(
        self,
        issue_number: int,
    ) -> Any:
        return await self.update_issue(
            issue_number=issue_number,
            state="closed",
        )

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

    async def create_comment(
        self,
        issue_number: int,
        body: str,
    ):
        url = (
            f"{self.issues_url}/"
            f"{issue_number}/comments"
        )

        response = await self._request(
            "POST",
            url,
            json={
                "body": body,
            },
        )

        return response.json()

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self.headers,
                **kwargs,
            )

        # GitHub can signal rate limiting with 403 or 429.
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