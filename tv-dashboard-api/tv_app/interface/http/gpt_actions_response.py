"""HTTP response helpers for the TV Custom GPT Actions façade.

Owned by the GPT façade interface layer — not Application. Routes and the TV
auth middleware share this shape so OpenAPI ``GptErrorEnvelope`` stays single.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from tv_app.core.serialize import json_safe


def correlation_id_from_request(request: Request | None) -> str:
    if request is None:
        return str(uuid.uuid4())
    raw = (
        request.headers.get("x-correlation-id")
        or request.headers.get("X-Correlation-Id")
        or ""
    ).strip()
    return raw or str(uuid.uuid4())


def gpt_fail(
    *,
    code: str,
    message: str,
    status_code: int,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "retryable": bool(retryable),
                "details": json_safe(details or {}),
            },
            "meta": {"correlationId": correlation_id or str(uuid.uuid4())},
        },
        headers=headers or None,
    )
