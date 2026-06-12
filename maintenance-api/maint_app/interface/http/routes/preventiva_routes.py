from fastapi import APIRouter, Query, Request

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.composition.maintenance_composer import build_preventiva_service
from maint_app.core.responses import fail, ok
from maint_app.interface.http.filial_access_http import resolve_access_scope

router = APIRouter(prefix="/maintenance/preventiva", tags=["Preventiva"])

_scope = FilialAccessScopeService()


@router.get("/alertas")
def list_alertas(request: Request, filial: str = Query(..., min_length=2, max_length=2)):
    scope = resolve_access_scope(request)
    try:
        _scope.assert_view_filial(scope, filial)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items = build_preventiva_service().listar_alertas(filial=filial)
    return ok({"items": items, "total": len(items)}, message="Alertas preventivos listados.")


@router.get("/historico")
def list_historico(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: str = Query(...),
):
    scope = resolve_access_scope(request)
    try:
        _scope.assert_view_filial(scope, filial)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items = build_preventiva_service().listar_historico(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        codigo_peca=codigo_peca,
    )
    return ok({"items": items, "total": len(items)}, message="Histórico listado.")
