from __future__ import annotations

import logging
import time

from fastapi import Request

from app.infrastructure.observability.request_context import (
    bind_request_context,
    reset_request_context,
)

logger = logging.getLogger("api_delpi.request")


def _resolve_operation_id(request: Request) -> str | None:
    route = request.scope.get("route")
    if route is None:
        return None

    operation_id = getattr(route, "operation_id", None)
    if isinstance(operation_id, str) and operation_id.strip():
        return operation_id.strip()

    return None


async def request_observability_middleware(request: Request, call_next):
    context_tokens = bind_request_context(request)
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        reset_request_context(context_tokens)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    operation_id = _resolve_operation_id(request)

    logger.info(
        "api_delpi_request method=%s path=%s status=%s operation_id=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        operation_id or "-",
        duration_ms,
    )

    if operation_id:
        response.headers["X-Operation-Id"] = operation_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    return response
