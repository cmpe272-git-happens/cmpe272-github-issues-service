from typing import Optional

from pydantic import BaseModel, Field


class IssueCreate(BaseModel):
    title: str = Field(..., min_length=1)
    body: Optional[str] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1)
