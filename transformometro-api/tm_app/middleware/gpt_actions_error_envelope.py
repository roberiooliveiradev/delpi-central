"""Normalize non-envelope HTTP errors on GPT Actions paths for Custom GPT."""

from __future__ import annotations

import json
import logging

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from tm_app.core.errors import envelope_from_detail_body
from tm_app.core.responses import fail

logger = logging.getLogger(__name__)


async def gpt_actions_error_envelope_middleware(request: Request, call_next):
    """Rewrite auth-style ``{detail}`` JSON into ApiEnvelope on /gpt-actions paths.

    JWT middleware returns ``{"detail": "Unauthorized"}``. Custom GPT often surfaces
    only the status code unless ``message`` is present in the Action response body.
    """
    response = await call_next(request)
    path = request.url.path or ""
    if "gpt-actions" not in path or response.status_code < 400:
        return response

    content_type = (response.headers.get("content-type") or "").lower()
    if "application/json" not in content_type:
        return response

    body_bytes = await _read_body(response)
    try:
        body = json.loads(body_bytes.decode("utf-8") or "null")
    except Exception:
        return _rebuild(response, body_bytes)

    converted = envelope_from_detail_body(
        status_code=response.status_code,
        body=body,
    )
    if converted is None:
        return _rebuild(response, body_bytes)

    message, data = converted
    return fail(message, response.status_code, data)


async def _read_body(response: Response) -> bytes:
    if hasattr(response, "body") and isinstance(response.body, (bytes, bytearray)):
        return bytes(response.body)
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:  # type: ignore[attr-defined]
        chunks.append(chunk if isinstance(chunk, (bytes, bytearray)) else bytes(chunk))
    return b"".join(chunks)


def _rebuild(response: Response, body_bytes: bytes) -> Response:
    headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-length", "content-type"}
    }
    return Response(
        content=body_bytes,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type or "application/json",
    )
