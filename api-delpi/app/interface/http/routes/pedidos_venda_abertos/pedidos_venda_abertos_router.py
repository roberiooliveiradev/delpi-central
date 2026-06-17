from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import PEDIDOS_VENDA_ABERTOS_PERMISSIONS
from app.composition.pedidos_venda_abertos_composer import (
    build_list_ops_abertas_use_case,
    build_list_pedidos_venda_abertos_use_case,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.utils.logger import log_error

router = APIRouter(
    prefix="/pedidos-venda-abertos",
    tags=["Pedidos de Venda em Aberto"],
)


@router.get(
    "/",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_pedidos_venda_abertos",
        path="/pedidos-venda-abertos/",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_pedidos_venda_abertos_route():
    try:
        use_case = build_list_pedidos_venda_abertos_use_case()
        result = use_case.execute()

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_pedidos_venda_abertos",
            message="Pedidos de venda em aberto carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar pedidos de venda em aberto: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar pedidos de venda em aberto: {exc}")
        return error_response(
            "Erro interno ao carregar pedidos de venda em aberto.",
            status_code=500,
        )


@router.get(
    "/ops-abertas",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_ops_abertas_pedidos_venda",
        path="/pedidos-venda-abertos/ops-abertas",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_ops_abertas_route():
    try:
        use_case = build_list_ops_abertas_use_case()
        result = use_case.execute()

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_ops_abertas_pedidos_venda",
            message="OPs abertas carregadas com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar OPs abertas: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar OPs abertas: {exc}")
        return error_response(
            "Erro interno ao carregar OPs abertas.",
            status_code=500,
        )
