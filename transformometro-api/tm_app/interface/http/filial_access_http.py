from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from tm_app.application.services.dashboard_view_scope_service import (
    DashboardView,
    DashboardViewScopeService,
)
from tm_app.application.services.filial_access_scope_service import (
    FilialAccessScope,
    FilialAccessScopeService,
)
from tm_app.core.responses import fail
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_scope_service = FilialAccessScopeService()
_view_scope = DashboardViewScopeService()


def resolve_access_scope(request: Request) -> FilialAccessScope:
    user = getattr(request.state, "user", None)
    return _scope_service.resolve(user)


def access_denied(message: str = "Sem permissão para acessar esta unidade.") -> JSONResponse:
    return fail(message, 403)


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
    scope = resolve_access_scope(request)
    try:
        dashboard_scope = _view_scope.resolve(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
        )
    except ValueError as exc:
        return fail(str(exc), 400)

    if dashboard_scope.view == DashboardView.CONSOLIDATED:
        if not _scope_service.can_view_consolidated(scope):
            return access_denied("Sem permissão para visão consolidada.")
        return None

    codigo = resolve_filial_codigo(dashboard_scope.filial_id)
    if not _scope_service.can_view_filial(scope, codigo):
        return access_denied()
    return None


def check_view_filial_access(
    request: Request,
    filial_ref: str | None,
) -> JSONResponse | None:
    scope = resolve_access_scope(request)
    codigo = resolve_filial_codigo(filial_ref)
    if not codigo:
        return fail("Unidade inválida.", 400)
    if not _scope_service.can_view_filial(scope, codigo):
        return access_denied()
    return None


def check_manage_filial_access(
    request: Request,
    filial_ref: str | None,
) -> JSONResponse | None:
    scope = resolve_access_scope(request)
    user = getattr(request.state, "user", None)
    codigo = resolve_filial_codigo(filial_ref)
    if not codigo:
        return fail("Unidade inválida.", 400)
    if not _scope_service.can_manage_filial(scope, codigo, user=user):
        return access_denied("Sem permissão para gerenciar dados nesta unidade.")
    return None


def check_processo_view_access(request: Request, processo_id: str) -> JSONResponse | None:
    scope = resolve_access_scope(request)
    if scope.is_unrestricted:
        return None
    instancias = ProcessoInstanciaRepository().list_by_processo(processo_id)
    if not instancias:
        return None
    if any(
        _scope_service.can_view_filial(scope, row.get("codigo_filial"))
        for row in instancias
    ):
        return None
    return access_denied()


def check_instancia_view_access(request: Request, instancia_id: str) -> JSONResponse | None:
    row = ProcessoInstanciaRepository().get(instancia_id)
    if not row:
        return None
    scope = resolve_access_scope(request)
    if row.get("todas_filiais_ativas"):
        if scope.is_unrestricted or _scope_service.can_view_consolidated(scope):
            return None
        return access_denied()
    if _scope_service.can_view_filial(scope, row.get("codigo_filial")):
        return None
    return access_denied()


def filter_rows_for_access(
    request: Request,
    rows: list[dict[str, Any]],
    *,
    codigo_key: str = "filial_id",
    alt_codigo_key: str | None = "codigo_filial",
) -> list[dict[str, Any]]:
    scope = resolve_access_scope(request)
    return _scope_service.filter_rows_by_filial(
        rows,
        scope,
        codigo_key=codigo_key,
        alt_codigo_key=alt_codigo_key,
    )


def require_unrestricted_catalog_admin(request: Request) -> JSONResponse | None:
    scope = resolve_access_scope(request)
    if scope.is_unrestricted:
        return None
    return access_denied("Operação restrita a perfis globais do Transformômetro.")
