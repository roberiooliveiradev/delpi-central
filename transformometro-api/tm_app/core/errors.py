from __future__ import annotations

import logging
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)

_logger = logging.getLogger(__name__)

_GENERIC_MESSAGE = "Erro interno do servidor."
_MAX_PUBLIC_MESSAGE = 480


def safe_public_message(message: str | None, *, limit: int = _MAX_PUBLIC_MESSAGE) -> str:
    """Truncate long public messages instead of collapsing them to a generic 500."""
    text = str(message or "").strip()
    if not text:
        return _GENERIC_MESSAGE
    if "For further information visit" in text:
        text = text.split("For further information visit", 1)[0].strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def format_api_error(exc: Exception) -> str:
    """Loga detalhes internos e retorna mensagem segura para o cliente."""
    _logger.debug("api_error_detail: %s", exc, exc_info=True)
    _status, message, _data = public_error_parts(exc)
    return message


def public_error_parts(exc: BaseException) -> tuple[int, str, dict[str, Any]]:
    """Map an exception to ``(status_code, message, data)`` for GPT/API clients.

    Always returns a human-readable ``message``. ``data`` includes ``error_kind``
    so Custom GPT can explain the failure instead of only the HTTP code.
    """
    # Duck-type GptActionsError to avoid circular import with dispatch_service.
    if type(exc).__name__ == "GptActionsError" and hasattr(exc, "message"):
        data = _as_error_data(getattr(exc, "data", None), error_kind="domain")
        status = int(getattr(exc, "status_code", 400) or 400)
        return status, safe_public_message(getattr(exc, "message", "")), data

    if _is_pydantic_validation_error(exc):
        message, data = format_validation_error(exc)
        data = {**data, "error_kind": "validation"}
        return 400, message, data

    if isinstance(exc, PermissionError):
        return 403, safe_public_message(str(exc) or "Acesso negado."), {
            "error_kind": "authz"
        }

    if isinstance(exc, LookupError) and not isinstance(exc, KeyError):
        return 404, safe_public_message(str(exc) or "Registro não encontrado."), {
            "error_kind": "not_found"
        }

    if isinstance(exc, KeyError):
        # Programming bug — do not claim "not found".
        return 500, _GENERIC_MESSAGE, {
            "error_kind": "internal",
            "error_type": type(exc).__name__,
        }

    if isinstance(exc, PluginsRepositoryError):
        return 503, safe_public_message(str(exc) or "Falha de persistência."), {
            "error_kind": "persistence"
        }

    if isinstance(exc, ValueError):
        return 400, safe_public_message(str(exc) or "Dados inválidos."), {
            "error_kind": "validation"
        }

    return 500, _GENERIC_MESSAGE, {
        "error_kind": "internal",
        "error_type": type(exc).__name__,
    }


def _as_error_data(data: Any, *, error_kind: str) -> dict[str, Any]:
    if isinstance(data, dict):
        out = dict(data)
        out.setdefault("error_kind", error_kind)
        return out
    if data is None:
        return {"error_kind": error_kind}
    return {"error_kind": error_kind, "details": data}


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
        return "Dados inválidos.", {"errors": [], "error_count": 0}

    missing = [i["field"] for i in items if "required" in i["reason"].lower()]
    if missing:
        headline = "Campos obrigatórios ausentes: " + ", ".join(missing)
    else:
        headline = "Dados inválidos: " + "; ".join(
            f"{i['field']} ({i['reason']})" for i in items[:6]
        )
    if len(items) > 6 and "Campos obrigatórios" not in headline:
        headline += f" (+{len(items) - 6} outros)"

    return safe_public_message(headline), {"errors": items, "error_count": len(items)}


def envelope_from_detail_body(
    *,
    status_code: int,
    body: Any,
) -> tuple[str, dict[str, Any]] | None:
    """Convert auth-style ``{detail: ...}`` JSON into envelope message+data."""
    if not isinstance(body, dict):
        return None
    if "success" in body and "message" in body:
        return None
    detail = body.get("detail")
    if detail is None and "message" not in body:
        return None
    if isinstance(detail, list):
        # FastAPI default validation shape
        class _Err:
            def errors(self_inner):  # noqa: N805
                return detail

        message, data = format_validation_error(_Err())
        data["error_kind"] = "validation"
        return message, data
    if isinstance(detail, dict):
        text = str(detail.get("message") or detail.get("msg") or detail)
    else:
        text = str(detail if detail is not None else body.get("message") or "")
    kind = "authn" if status_code == 401 else "authz" if status_code == 403 else "http"
    if status_code >= 500:
        kind = "internal"
    return safe_public_message(text or _GENERIC_MESSAGE), {"error_kind": kind}
