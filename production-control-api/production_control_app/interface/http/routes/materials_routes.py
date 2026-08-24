from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import (
    build_finished_product_shortage_service,
    build_materials_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    InvalidProductCode,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Materials"])


@router.get("/materials")
def get_materials(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    view: str = Query("excess", description="excess ou shortage"),
    search: str = Query("", description="Produto, solicitação ou fornecedor"),
    sort: str | None = Query(None),
    direction: str = Query("asc"),
    page: int = Query(1, ge=1),
    pageSize: int | None = Query(None, alias="pageSize", ge=1, le=200),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    user = resolve_user(request)
    try:
        data = build_materials_service().list_materials(
            user,
            branch=branch,
            view=view,
            search=search,
            sort=sort,
            direction=direction,
            page=page,
            page_size=pageSize,
            refresh=refresh,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)


@router.get("/materials/finished-product-shortages")
def get_finished_product_shortages(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    product: str = Query(..., description="Código do PA"),
    status: str = Query("all", description="shortage, no_commitment, ok ou all"),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    user = resolve_user(request)
    try:
        data = build_finished_product_shortage_service().get_shortages(
            user,
            branch=branch,
            product=product,
            status=status,
            refresh=refresh,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except InvalidProductCode as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)
