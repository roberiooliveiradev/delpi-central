from typing import Optional

from fastapi import APIRouter, Query, Request

from delpi_api_client import DelpiApiError

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import assert_submodule_view
from maint_app.composition.maintenance_composer import build_mini_applicators_totvs_gateway
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user

router = APIRouter(prefix="/maintenance/mini-aplicadores", tags=["Mini-aplicadores"])

_scope = FilialAccessScopeService()
_SUBMODULE_ID = "mini-aplicadores"


@router.get("/ferramentas")
def list_ferramentas(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=200),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.listar_ferramentas(
            codigo=codigo,
            descricao=descricao,
            filial=filial,
            page=page,
            page_size=page_size,
        )
        return ok(data, message="Ferramentas listadas.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


@router.get("/ferramentas/{codigo}")
def get_ferramenta(request: Request, codigo: str, filial: str = Query(..., min_length=2, max_length=2)):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.obter_ferramenta(codigo)
        return ok(data, message="Ferramenta encontrada.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


@router.get("/ferramentas/{codigo}/pecas")
def list_pecas(request: Request, codigo: str, filial: str = Query(..., min_length=2, max_length=2)):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.listar_pecas(codigo)
        return ok(data, message="Peças listadas.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


@router.get("/ferramentas/{codigo}/componentes")
def list_componentes(request: Request, codigo: str, filial: str = Query(..., min_length=2, max_length=2)):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.listar_componentes(codigo_ferramenta=codigo, filial=filial)
        return ok(data, message="Componentes listados.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)
