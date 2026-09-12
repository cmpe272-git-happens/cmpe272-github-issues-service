import os
from dotenv import load_dotenv
from dotenv import load_dotenv

load_dotenv()


class Settings:
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_owner: str = os.getenv("GITHUB_OWNER", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
