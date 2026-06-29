from typing import Optional

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission

from app.application.dto.customer.search_customers_request import SearchCustomersRequest
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.composition.customer_composer import build_search_customers_use_case
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/customers", tags=["Clientes"])


@router.get("/search")
@require_permission(API_DELPI_ACCESS)
def search_customers_route(
    code: Optional[str] = Query(None, description="Código do cliente (SA1)."),
    name: Optional[str] = Query(None, description="Nome ou parte do nome."),
    store: Optional[str] = Query(None, description="Loja do cliente."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        if not any(part.strip() for part in ((code or ""), (name or ""), (store or ""))):
            return error_response("Informe code, name ou store para buscar clientes.")

        use_case = build_search_customers_use_case()
        result = use_case.execute(
            SearchCustomersRequest(
                code=code,
                name=name,
                store=store,
                page=page,
                page_size=page_size,
            )
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="search_customers",
            entity="customer_search",
            shape="paged_list",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar clientes: {exc}")
        return error_response(str(exc))
