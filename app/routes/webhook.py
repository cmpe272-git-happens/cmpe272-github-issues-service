"""
GitHub webhook receiver and HMAC verification.

Author: Sukruti Shah
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.database import save_event

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


def verify_signature(payload: bytes, signature: str | None) -> bool:
    """
    Verify that the webhook request really came from GitHub.
    """

    webhook_secret = os.getenv("WEBHOOK_SECRET")

    if not webhook_secret:
        return False

    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
    x_github_event: str | None = Header(
        default=None,
        alias="X-GitHub-Event",
    ),
    x_github_delivery: str | None = Header(
        default=None,
        alias="X-GitHub-Delivery",
    ),
):
    # Read the exact raw body GitHub sent.
    payload_bytes = await request.body()

    # 1. Verify that the request really came from GitHub.
    if not verify_signature(
        payload_bytes,
        x_hub_signature_256,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    # 2. Only accept events required by the assignment.
    allowed_events = {
        "issues",
        "issue_comment",
        "ping",
    }

    if x_github_event not in allowed_events:
        raise HTTPException(
            status_code=400,
            detail="Unsupported GitHub event",
        )

    # 3. Every GitHub delivery should have a unique delivery ID.
    if not x_github_delivery:
        raise HTTPException(
            status_code=400,
            detail="Missing GitHub delivery ID",
        )

    # 4. Parse the JSON payload.
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    # 5. Decide the action and issue number.
    if x_github_event == "ping":
        # GitHub ping payloads do not have normal issue actions.
        action = "ping"
        issue_number = None

    else:
        action = payload.get("action")

        if not action:
            raise HTTPException(
                status_code=400,
                detail="Missing webhook action",
            )

        issue_number = payload.get("issue", {}).get("number")

    # 6. Store the webhook event.
    timestamp = datetime.now(timezone.utc).isoformat()

    save_event(
        delivery_id=x_github_delivery,
        event=x_github_event,
        action=action,
        issue_number=issue_number,
        timestamp=timestamp,
    )

    # 7. Acknowledge quickly.
    return Response(status_code=204)