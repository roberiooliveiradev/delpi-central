from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from delpi_api_client import DelpiApiError

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import assert_submodule_view
from maint_app.composition.maintenance_composer import build_mini_applicators_totvs_gateway
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user
from maint_app.interface.http.list_query_params import list_query_params
from maint_app.application.list_query import ListQuery, paginate_slice

router = APIRouter(prefix="/maintenance/mini-aplicadores", tags=["Mini-aplicadores"])

_scope = FilialAccessScopeService()
_SUBMODULE_ID = "mini-aplicadores"
_PECA_REPOSICAO_PREFIX = "3019"


def _filter_pecas_reposicao(items: list) -> list[dict]:
    """Peças substituíveis: amarradas à ferramenta (SG1010) com código 3019*."""
    return [
        item
        for item in items
        if str(item.get("codigo") or "").strip().startswith(_PECA_REPOSICAO_PREFIX)
    ]


def _sort_componentes(items: list, sort_by: str | None, sort_dir: str) -> list:
    reverse = sort_dir == "desc"
    key_name = (sort_by or "nivel").strip().lower()

    def sort_key(item: dict) -> str | float | int:
        if key_name == "codigo":
            return str(item.get("codigo") or "")
        if key_name == "descricao":
            return str(item.get("descricao") or "")
        if key_name == "unidade":
            return str(item.get("unidade") or "")
        if key_name == "estoque01":
            return float(item.get("estoque_local_01") or 0)
        if key_name == "estoque99":
            return float(item.get("estoque_local_99") or 0)
        return int(item.get("nivel") or 0)

    return sorted(items, key=sort_key, reverse=reverse)


@router.get("/ferramentas")
def list_ferramentas(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
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
            page=query.page,
            page_size=query.page_size,
            sort_by=query.sort_by,
            sort_dir=query.sort_dir,
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
        items = _filter_pecas_reposicao(data.get("items") or [])
        return ok({"items": items, "total": len(items)}, message="Peças de reposição (3019) listadas.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


@router.get("/ferramentas/{codigo}/componentes")
def list_componentes(
    request: Request,
    codigo: str,
    filial: str = Query(..., min_length=2, max_length=2),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.listar_componentes(codigo_ferramenta=codigo, filial=filial)
        items = _sort_componentes(data.get("items") or [], query.sort_by, query.sort_dir)
        page_items, total = paginate_slice(items, query)
        return ok({"items": page_items, "total": total}, message="Componentes amarrados listados.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)
