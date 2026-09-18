"""Gates HTTP do Transformômetro.

Filial não autoriza. Quem tem access vê todas as unidades.
O filtro analítico da Visão geral continua em DashboardViewScopeService.
O dicionário access_scope devolvido ao portal é só forma do filtro:
mode unrestricted significa que o seletor pode mostrar Todas.
Não é escopo de autorização.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.application.services.dashboard_view_scope_service import (
    DashboardViewScopeService,
)
from tm_app.core.responses import fail
from tm_app.infrastructure.persistence.repositories.branch_repository import FilialRepository

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_view_scope = DashboardViewScopeService()

# Forma antiga do seletor. Não lista unidades autorizadas.
PORTAL_FILTER_META: dict[str, Any] = {
    "mode": "unrestricted",
    "allowed_filiais": [],
    "can_view_consolidated": True,
    "scoped_manage": False,
}


def _policy() -> TransformometroAuthorizationPolicy:
    return TransformometroAuthorizationPolicy()


def _user(request: Request) -> Any | None:
    return getattr(request.state, "user", None)


def _as_response(exc: AuthorizationDenied) -> JSONResponse:
    return fail(str(exc), exc.status_code)


def require_transformometro_view_access(request: Request) -> JSONResponse | None:
    """Uso normal do portal. Só transformometro.access."""
    try:
        _policy().require_access(_user(request))
    except AuthorizationDenied as exc:
        return _as_response(exc)
    return None


def require_portal_manage(request: Request) -> JSONResponse | None:
    """CRUD do catálogo em Administração. Não abre o uso normal."""
    try:
        _policy().require_manage(_user(request))
    except AuthorizationDenied as exc:
        return _as_response(exc)
    return None


def resolve_filial_codigo(filial_ref: str | None) -> str | None:
    if not filial_ref:
        return None
    ref = str(filial_ref).strip()
    if not ref:
        return None
    if _UUID_PATTERN.match(ref):
        try:
            UUID(ref)
        except ValueError:
            return None
        row = FilialRepository().get(ref)
        if not row:
            return None
        return str(row.get("codigo_filial") or "").strip() or None
    return ref


def check_dashboard_filial_access(
    request: Request,
    *,
    view: str | None,
    filial_id: str | None,
    setor_id: str | None,
) -> JSONResponse | None:
    """Access abre Todas, 01, 02 e futuras. Filial só valida o parâmetro da consulta."""
    if denied := require_transformometro_view_access(request):
        return denied
    try:
        _view_scope.resolve(view=view, filial_id=filial_id, setor_id=setor_id)
    except ValueError as exc:
        return fail(str(exc), 400)
    return None


def check_view_filial_access(
    request: Request,
    filial_ref: str | None,
) -> JSONResponse | None:
    if denied := require_transformometro_view_access(request):
        return denied
    if not resolve_filial_codigo(filial_ref):
        return fail("Unidade inválida.", 400)
    return None


def check_manage_filial_access(
    request: Request,
    filial_ref: str | None,
) -> JSONResponse | None:
    """Escrita normal do ciclo. Unidade do registro não autoriza nem esconde."""
    if denied := require_transformometro_view_access(request):
        return denied
    if filial_ref and not resolve_filial_codigo(filial_ref):
        return fail("Unidade inválida.", 400)
    return None


def check_processo_view_access(request: Request, processo_id: str) -> JSONResponse | None:
    del processo_id
    return require_transformometro_view_access(request)


def check_processo_manage_access(request: Request, processo_id: str) -> JSONResponse | None:
    del processo_id
    return require_transformometro_view_access(request)


def check_instancia_view_access(request: Request, instancia_id: str) -> JSONResponse | None:
    del instancia_id
    return require_transformometro_view_access(request)


def check_instancia_manage_access(request: Request, instancia_id: str) -> JSONResponse | None:
    del instancia_id
    return require_transformometro_view_access(request)


def filter_rows_for_access(
    request: Request,
    rows: list[dict[str, Any]],
    *,
    codigo_key: str = "filial_id",
    alt_codigo_key: str | None = "codigo_filial",
) -> list[dict[str, Any]]:
    del codigo_key, alt_codigo_key
    if not _policy().has_access(_user(request)):
        return []
    return list(rows)
