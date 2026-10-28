"""Request observability — correlation id, operation id, tempo, log estruturado.

Padrão canônico: api-delpi ``request_observability_middleware`` +
``X-Request-Id`` de supplies/delia/external-data. Somente metadados
operacionais são registrados — nunca Authorization, tokens, bodies, cookies
ou query strings.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextvars import ContextVar

from fastapi import Request

logger = logging.getLogger("engineering_api.request")

REQUEST_ID_HEADER = "X-Request-Id"
# Alias aceito como entrada (precedência canônica de external-data);
# a saída oficial é sempre X-Request-Id.
CORRELATION_ID_ALIAS = "X-Correlation-Id"

_REQUEST_ID_MAX_LENGTH = 128
_REQUEST_ID_SAFE = re.compile(r"^[A-Za-z0-9._~:-]+$")
# Classificação genérica para paths sem rota — nunca deriva de input.
_OPERATION_UNMATCHED = "unmatched_route"

_request_id_ctx: ContextVar[str | None] = ContextVar(
    "engineering_request_id", default=None
)


def get_request_id() -> str | None:
    """Request id do contexto corrente (logs, handlers, futura propagação)."""
    return _request_id_ctx.get()


def _resolve_request_id(request: Request) -> str:
    """Preserva id recebido somente se válido; caso contrário gera uuid4.

    IDs com caracteres de controle, fora do charset seguro ou acima do
    limite são descartados — nunca refletidos na resposta.
    """
    for header in (REQUEST_ID_HEADER, CORRELATION_ID_ALIAS):
        raw = (request.headers.get(header) or "").strip()
        if (
            raw
            and len(raw) <= _REQUEST_ID_MAX_LENGTH
            and _REQUEST_ID_SAFE.fullmatch(raw)
        ):
            return raw
    return str(uuid.uuid4())


def _resolve_operation_id(request: Request) -> str | None:
    route = request.scope.get("route")
    if route is None:
        return None
    operation_id = getattr(route, "operation_id", None)
    if isinstance(operation_id, str) and operation_id.strip():
        return operation_id.strip()
    return None


def _safe_path(path: str) -> str:
    """Neutraliza caracteres de controle (log forging via path decodificado)."""
    return "".join(c if c.isprintable() else "?" for c in path)


async def request_observability_middleware(request: Request, call_next):
    request_id = _resolve_request_id(request)
    ctx_token = _request_id_ctx.set(request_id)
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.error(
            "engineering_api_request method=%s path=%s request_id=%s "
            "duration_ms=%s error_class=%s",
            request.method,
            _safe_path(request.url.path),
            request_id,
            duration_ms,
            type(exc).__name__,
        )
        raise
    finally:
        _request_id_ctx.reset(ctx_token)

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    operation_id = _resolve_operation_id(request)
    status_class = f"{response.status_code // 100}xx"

    logger.info(
        "engineering_api_request method=%s path=%s status=%s "
        "operation_id=%s request_id=%s duration_ms=%s result=%s",
        request.method,
        _safe_path(request.url.path),
        response.status_code,
        operation_id or _OPERATION_UNMATCHED,
        request_id,
        duration_ms,
        status_class,
    )

    response.headers[REQUEST_ID_HEADER] = request_id
    if operation_id:
        response.headers["X-Operation-Id"] = operation_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response
