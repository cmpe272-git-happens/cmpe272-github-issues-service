"""
Pydantic request schemas for the GitHub Issues Service.

The schemas:
* validate issue creation requests, including required non-empty titles;
* validate issue update requests and restrict issue state to ``open`` or
  ``closed``;
* validate optional issue bodies and labels; and
* validate comment creation requests with a required non-empty body.

Author: Navaneeth Puklath, Juilee Giramkar
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class IssueCreate(BaseModel):
    title: str = Field(..., min_length=1)
    body: Optional[str] = None
    labels: Optional[list[str]] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[Literal["open", "closed"]] = None


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1)
