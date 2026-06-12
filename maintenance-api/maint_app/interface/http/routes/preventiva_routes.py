from fastapi import APIRouter, Depends, Query, Request

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import assert_submodule_view
from maint_app.composition.maintenance_composer import build_preventiva_service
from maint_app.core.responses import fail, ok
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user
from maint_app.interface.http.list_query_params import list_query_params
from maint_app.application.list_query import ListQuery

router = APIRouter(prefix="/maintenance/preventiva", tags=["Preventiva"])

_scope = FilialAccessScopeService()
_SUBMODULE_ID = "mini-aplicadores"


@router.get("/resumo")
def resumo_alertas(request: Request, filial: str = Query(..., min_length=2, max_length=2)):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    data = build_preventiva_service().resumo_alertas(filial=filial)
    return ok(data, message="Resumo preventivo calculado.")


@router.get("/alertas")
def list_alertas(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    ferramenta: str | None = Query(None),
    peca: str | None = Query(None),
    status: list[str] | None = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items, total = build_preventiva_service().listar_alertas(
        filial=filial,
        query=query,
        ferramenta=ferramenta,
        peca=peca,
        statuses=status,
    )
    return ok({"items": items, "total": total}, message="Alertas preventivos listados.")


@router.get("/historico")
def list_historico(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: str = Query(...),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items = build_preventiva_service().listar_historico(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        codigo_peca=codigo_peca,
    )
    return ok({"items": items, "total": len(items)}, message="Histórico listado.")


@router.get("/ultimas-reposicoes")
def list_ultimas_reposicoes(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    ferramenta: str | None = Query(None),
    peca: str | None = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items, total = build_preventiva_service().listar_ultimas_reposicoes(
        filial=filial,
        query=query,
        ferramenta=ferramenta,
        peca=peca,
    )
    return ok({"items": items, "total": total}, message="Últimas reposições listadas.")
