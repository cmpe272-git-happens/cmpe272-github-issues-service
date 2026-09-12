from typing import Any

import httpx

from app.config import settings


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
    ):
        self.token = token or settings.github_token
        self.owner = owner or settings.github_owner
        self.repo = repo or settings.github_repo

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @property
    def issues_url(self) -> str:
        return f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/issues"

    async def list_issues(self) -> Any:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.issues_url,
                headers=self.headers,
            )

        response.raise_for_status()
        return response.json()

    async def get_issue(self, issue_number: int) -> Any:
        url = f"{self.issues_url}/{issue_number}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
            )

        response.raise_for_status()
        return response.json()

    async def create_issue(
        self,
        title: str,
        body: str | None = None,
    ) -> Any:
        payload = {
            "title": title,
        }

        if body is not None:
            payload["body"] = body

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.issues_url,
                headers=self.headers,
                json=payload,
            )

        response.raise_for_status()
        return response.json()

    async def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> Any:
        payload = {}

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["body"] = body

        if state is not None:
            payload["state"] = state

        url = f"{self.issues_url}/{issue_number}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self.headers,
                json=payload,
            )

        response.raise_for_status()
        return response.json()

    async def close_issue(self, issue_number: int) -> Any:
        return await self.update_issue(
            issue_number=issue_number,
            state="closed",
        )

        async def list_comments(self, issue_number: int) -> Any:
        url = f"{self.issues_url}/{issue_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
            )

        response.raise_for_status()
        return response.json()

    async def create_comment(
        self,
        issue_number: int,
        body: str,
    ) -> Any:
        url = f"{self.issues_url}/{issue_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json={"body": body},
            )

        response.raise_for_status()
        return response.json()
