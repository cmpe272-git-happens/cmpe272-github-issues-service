"""
Application configuration for the GitHub Issues Service.

The configuration:
* loads environment variables from the ``.env`` file;
* stores the GitHub personal access token, repository owner, and repository name;
* stores the webhook secret used for webhook validation; and
* configures the application port.

Author: Thanzeel Hassan
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_owner: str = os.getenv("GITHUB_OWNER", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
