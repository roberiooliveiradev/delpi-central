from __future__ import annotations

from fastapi import Request

REQUESTS_CLIENT_ID_HEADER = "X-My-Requests-Client-Id"


def client_id_from_request(request: Request) -> str | None:
    raw = request.headers.get(REQUESTS_CLIENT_ID_HEADER) or ""
    cleaned = raw.strip()
    return cleaned or None
