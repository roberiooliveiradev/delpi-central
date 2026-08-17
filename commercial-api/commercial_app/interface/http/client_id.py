from __future__ import annotations

from fastapi import Request

COMMERCIAL_CLIENT_ID_HEADER = "X-Commercial-Client-Id"


def client_id_from_request(request: Request) -> str | None:
    raw = request.headers.get(COMMERCIAL_CLIENT_ID_HEADER) or ""
    cleaned = raw.strip()
    return cleaned or None
