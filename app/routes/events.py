"""
Webhook event debugging endpoint.

Author: Sukruti Shah
"""

from fastapi import APIRouter, Query

from app.database import get_events

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("")
def list_events(
    limit: int = Query(default=50, ge=1, le=100),
):
    return get_events(limit)