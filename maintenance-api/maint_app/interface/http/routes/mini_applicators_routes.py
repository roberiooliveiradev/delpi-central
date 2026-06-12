from typing import Optional

from fastapi import APIRouter, Query

from delpi_api_client import DelpiApiError

from maint_app.composition.maintenance_composer import build_mini_applicators_totvs_gateway
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok

router = APIRouter(prefix="/maintenance/mini-aplicadores", tags=["Mini-aplicadores"])


@router.get("/ferramentas")
def list_ferramentas(
    codigo: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=200),
):
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
def get_ferramenta(codigo: str):
    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.obter_ferramenta(codigo)
        return ok(data, message="Ferramenta encontrada.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)
