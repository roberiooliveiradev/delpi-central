from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def success_envelope(data: Any, message: str = "OK") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data, "error": None, "meta": {}}


def error_envelope(
    code: str,
    message: str,
    request_id: str,
    *,
    recoverable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "recoverable": recoverable,
            "details": details or {},
        },
        "meta": {"request_id": request_id},
    }


def error_response(
    status: int,
    code: str,
    message: str,
    request_id: str,
    *,
    recoverable: bool = False,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=error_envelope(
            code, message, request_id, recoverable=recoverable, details=details
        ),
        headers=headers,
    )
