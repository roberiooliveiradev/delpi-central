"""JWT do Portal Financeiro — health público mesmo com ASGI root_path.

O token de serviço interno só entra nas rotas de NF-e recebida. Nas demais
rotas ele não vira superadmin nem substitui o JWT do usuário.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path
from delpi_auth.service_token import request_has_valid_internal_service_token

__all__ = ["jwt_middleware"]

_RECEIVED_INVOICE_PREFIX = "/invoices/received"


def _is_public_health(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "/health":
        return True
    # uvicorn --root-path /apps/financial-api → path completo no middleware
    return normalized.endswith("/financial-api/health")


def _is_received_invoice_path(path: str) -> bool:
    normalized = normalize_path(path)
    index = normalized.find(_RECEIVED_INVOICE_PREFIX)
    if index < 0:
        return False
    suffix = normalized[index:]
    return suffix == _RECEIVED_INVOICE_PREFIX or suffix.startswith(f"{_RECEIVED_INVOICE_PREFIX}/")


def _internal_invoice_reader() -> SimpleNamespace:
    return SimpleNamespace(
        id="internal-service",
        email="service@delpi.internal",
        name="Serviço Interno",
        roles=[],
        groups=[],
        permissions=[],
        is_superadmin=False,
        rbac_unavailable=False,
        access_token=None,
        principal_type="service",
        internal_invoice_reader=True,
    )


async def jwt_middleware(request: Request, call_next):
    if _is_public_health(request.url.path):
        return await call_next(request)
    if request_has_valid_internal_service_token(request):
        if not _is_received_invoice_path(request.url.path):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        request.state.user = _internal_invoice_reader()
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
