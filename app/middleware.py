"""
Request ID and structured logging middleware for the GitHub Issues Service.

The middleware:
* generates a unique request ID when one is not provided by the client;
* preserves an existing ``X-Request-ID`` header;
* records the HTTP method, endpoint, status code, and request latency;
* includes the request ID in the response headers; and
* logs unexpected exceptions with a 500 status and request context.

Author: Thanzeel Hassan
"""

import json
import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("github_issues_service")

SERVICE_NAME = "github-issues-service"


async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        log_data = {
            "service": SERVICE_NAME,
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
        }

        logger.info(json.dumps(log_data))

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        log_data = {
            "service": SERVICE_NAME,
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status": 500,
            "latency_ms": latency_ms,
        }

        logger.exception(json.dumps(log_data))

        raise
