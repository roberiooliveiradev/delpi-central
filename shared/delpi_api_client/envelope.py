"""Parsing do envelope JSON da api-delpi."""

from __future__ import annotations

from typing import Any


def parse_envelope(body: Any) -> tuple[Any, dict[str, Any] | None, dict[str, Any] | None]:
    """Retorna `(data, meta, error)` com fallback para corpo cru."""
    if not isinstance(body, dict):
        return body, None, None

    if "success" in body or "data" in body:
        meta = body.get("meta")
        error = body.get("error")
        return (
            body.get("data"),
            meta if isinstance(meta, dict) else None,
            error if isinstance(error, dict) else None,
        )

    return body, None, None


def format_error_message(body: Any, *, fallback: str = "Erro na api-delpi") -> str:
    if not isinstance(body, dict):
        return fallback

    message = body.get("message")
    detail = body.get("detail")
    base = message if isinstance(message, str) and message.strip() else None
    if base is None and isinstance(detail, str) and detail.strip():
        base = detail
    if base is None:
        base = fallback

    error = body.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, str) and code:
            return f"[{code}] {base}"

    return base
