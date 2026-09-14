"""
Health check endpoint for the GitHub Issues Service.

The endpoint:
* provides a lightweight health check at ``/healthz``; and
* returns a successful response when the service is running.

Author: Thanzeel Hassan
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
