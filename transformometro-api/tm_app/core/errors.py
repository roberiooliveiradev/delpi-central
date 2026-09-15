from __future__ import annotations

import logging
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)

_logger = logging.getLogger(__name__)

_GENERIC_MESSAGE = "Erro interno do servidor."
_MAX_PUBLIC_MESSAGE = 480


def format_api_error(exc: Exception) -> str:
    """Loga detalhes internos e retorna mensagem segura para o cliente."""
    _logger.debug("api_error_detail: %s", exc, exc_info=True)

    if _is_pydantic_validation_error(exc):
        message, _data = format_validation_error(exc)
        return message

    if isinstance(exc, (ValueError, PluginsRepositoryError)):
        msg = str(exc)
        if msg and len(msg) < 300:
            return msg

    return _GENERIC_MESSAGE


def _is_pydantic_validation_error(exc: BaseException) -> bool:
    # Avoid hard import dependency at module import for non-pydantic paths.
    cls = type(exc)
    if cls.__name__ == "ValidationError" and "pydantic" in (cls.__module__ or ""):
        return True
    # RequestValidationError wraps the same error shape via .errors().
    if hasattr(exc, "errors") and callable(getattr(exc, "errors")):
        module = type(exc).__module__ or ""
        if "fastapi" in module or "pydantic" in module or "starlette" in module:
            try:
                errors = exc.errors()  # type: ignore[attr-defined]
            except Exception:
                return False
            return isinstance(errors, list)
    return False


def format_validation_error(exc: BaseException) -> tuple[str, dict[str, Any]]:
    """Human-readable validation summary for GPT Actions / API clients.

    Returns ``(message, data)`` where ``data.errors`` lists field/path + reason.
    Never returns only an HTTP status code — Custom GPT must receive the text.
    """
    raw_errors: list[Any]
    try:
        raw_errors = list(exc.errors())  # type: ignore[attr-defined]
    except Exception:
        raw_errors = []

    items: list[dict[str, str]] = []
    for err in raw_errors:
        if not isinstance(err, dict):
            continue
        loc = err.get("loc") or ()
        parts = [str(p) for p in loc if p not in {"body", "query", "path"}]
        field = ".".join(parts) if parts else "(root)"
        msg = str(err.get("msg") or "inválido")
        # Drop pydantic doc URLs from the public message.
        if "For further information visit" in msg:
            msg = msg.split("For further information visit", 1)[0].strip()
        items.append({"field": field, "reason": msg})

    if not items:
        return "Dados inválidos.", {"errors": []}

    missing = [i["field"] for i in items if "required" in i["reason"].lower()]
    if missing:
        headline = "Campos obrigatórios ausentes: " + ", ".join(missing)
    else:
        headline = "Dados inválidos: " + "; ".join(
            f"{i['field']} ({i['reason']})" for i in items[:6]
        )
    if len(items) > 6 and "Campos obrigatórios" not in headline:
        headline += f" (+{len(items) - 6} outros)"

    if len(headline) > _MAX_PUBLIC_MESSAGE:
        headline = headline[: _MAX_PUBLIC_MESSAGE - 1] + "…"

    return headline, {"errors": items, "error_count": len(items)}
