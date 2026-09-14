"""
Debugging endpoint for persisted GitHub webhook events.

This module exposes the GET /events endpoint, which retrieves recently
processed webhook deliveries from the SQLite event store. The endpoint
supports a configurable result limit between 1 and 100 events and returns
the newest persisted events first.

It is intended primarily for debugging and verifying that GitHub webhook
deliveries have been successfully received and persisted.

Author: Sukruti Shah
"""

from fastapi import APIRouter, Query

from app.database import get_events

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("")
def list_events(
    limit: int = Query(default=20, ge=1, le=100),
):
    return get_events(limit)
