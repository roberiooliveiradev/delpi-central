from typing import Optional

from fastapi import APIRouter, Body, File, Path, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS,
    PEDIDOS_VENDA_ABERTOS_PERMISSIONS,
)
from app.application.use_cases.pedidos_venda_abertos.enrich_portfolio_customers_use_case import (
    EnrichCustomersRequest,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case import (
    ListCustomerBillingSeriesRequest,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_open_order_metrics_use_case import (
    ListCustomerOpenOrderMetricsRequest,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_outbound_invoices_use_case import (
    ListCustomerOutboundInvoicesRequest,
)
from app.application.use_cases.pedidos_venda_abertos.manage_seller_portfolio_use_case import (
    CreateSellerRequest,
    parse_customer_assignments,
    portfolio_to_dict,
)
from app.application.use_cases.pedidos_venda_abertos.search_active_customers_use_case import (
    SearchActiveCustomersRequest,
)
from app.composition.pedidos_venda_abertos_composer import (
    build_enrich_portfolio_customers_use_case,
    build_list_customer_billing_series_use_case,
    build_list_customer_open_order_metrics_use_case,
    build_list_customer_outbound_invoices_use_case,
    build_list_ops_abertas_use_case,
    build_list_pedidos_venda_abertos_use_case,
    build_manage_customer_avatar_use_case,
    build_manage_seller_portfolio_use_case,
    build_resolve_portfolio_scope_use_case,
    build_search_active_customers_use_case,
)
from app.core.responses import error_response
from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.pedidos_venda_abertos.portfolio_access import (
    can_filter_by_seller_id,
    current_user_id,
    is_portfolio_admin,
    is_portfolio_unrestricted,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/pedidos-venda-abertos",
    tags=["Pedidos de Venda em Aberto"],
)

# Rotas /sellers* e /customers/*/avatar (CRUD Delpi) estão **deprecated** para novos
# consumidores — canônico: commercial-api (/apps/commercial-api/seller-portfolios*,
# /customers/*/avatar). Mantidas read/write até cutover F2c (COMMERCIAL_PORTFOLIO_SOURCE).
# Reads TOTVS (listagens, search, enrichment, billing, NF) permanecem nesta api-delpi
# como SQL parametrizado. Escopo de carteira do **Portal** = commercial-api BFF
# (SCOPE-OWNERSHIP). `ResolvePortfolioScope` / `_resolve_scope` abaixo é **legado PVA**
# até F2c — não evoluir para o Portal.


class SellerCustomerBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)
    customer_name: Optional[str] = None


class CreateSellerBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    customers: list[SellerCustomerBody] = Field(default_factory=list)


class UpdateSellerBody(BaseModel):
    display_name: Optional[str] = None
    active: Optional[bool] = None


class ReplaceCustomersBody(BaseModel):
    customers: list[SellerCustomerBody] = Field(default_factory=list)


class TransferCustomersBody(BaseModel):
    target_seller_id: str = Field(..., min_length=1)
    customers: list[SellerCustomerBody] = Field(..., min_length=1)


class EnrichCustomerRefBody(BaseModel):
    customer_code: str = Field(..., min_length=1)
    customer_store: str = Field(..., min_length=1)


class EnrichCustomersBody(BaseModel):
    customers: list[EnrichCustomerRefBody] = Field(default_factory=list, max_length=200)


class OpenOrderMetricsBody(BaseModel):
    """Optional customer keys; empty/omitted = full open-orders universe."""

    customers: list[EnrichCustomerRefBody] = Field(default_factory=list, max_length=500)


class BillingSeriesBody(BaseModel):
    customers: list[EnrichCustomerRefBody] = Field(default_factory=list, max_length=200)
    months: int = Field(default=12, ge=1, le=24)
    start_date: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Inclusive start date (YYYY-MM-DD). Requires end_date.",
    )
    end_date: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Inclusive end date (YYYY-MM-DD). Requires start_date.",
    )
    granularity: Optional[str] = Field(
        default=None,
        pattern=r"^(day|week|month|year)$",
        description="Series bucket size: day, week, month or year.",
    )


def _resolve_scope(seller_id: Optional[str] = None):
    """Escopo PVA (membership JWT). Portal Comercial NÃO usa esta rota para listagem TOTVS."""
    can_filter = can_filter_by_seller_id()
    seller_filter = (seller_id or "").strip() or None
    # team.view pode filtrar uma carteira; manage sem filtro vê consolidado.
    unrestricted = is_portfolio_unrestricted() or (can_filter and bool(seller_filter))
    return build_resolve_portfolio_scope_use_case().execute(
        user_id=current_user_id(),
        is_unrestricted=unrestricted,
        seller_id_filter=seller_filter if can_filter else None,
    )


@router.get(
    "/",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_pedidos_venda_abertos",
        path="/pedidos-venda-abertos/",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_pedidos_venda_abertos_route(
    seller_id: Optional[str] = Query(
        None,
        description="Filtro de carteira (team.view, admin/gerente).",
    ),
):
    try:
        if seller_id and not can_filter_by_seller_id():
            return error_response(
                "Filtro por vendedor disponível apenas para equipe ou gerentes.",
                status_code=403,
            )
        scope = _resolve_scope(seller_id)
        use_case = build_list_pedidos_venda_abertos_use_case()
        result = use_case.execute(scope)

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_pedidos_venda_abertos",
            message="Pedidos de venda em aberto carregados com sucesso.",
        )

    except LookupError as exc:
        return error_response(str(exc), status_code=404)
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
    "/totvs-open-orders",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_totvs_open_orders",
        path="/pedidos-venda-abertos/totvs-open-orders",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_totvs_open_orders_route():
    """
    Leitura TOTVS pura (sem membership/carteira) — consumo BFF commercial-api.
    Reusa ListPedidosVendaAbertosUseCase com scope=None. Não altera regras da rota `/`.
    """
    try:
        use_case = build_list_pedidos_venda_abertos_use_case()
        result = use_case.execute(scope=None)
        return api_delpi_success(
            result.to_dict(),
            operation_id="list_totvs_open_orders",
            message="Pedidos de venda em aberto (TOTVS) carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar pedidos TOTVS: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao listar pedidos TOTVS: {exc}")
        return error_response(
            "Erro interno ao carregar pedidos de venda em aberto (TOTVS).",
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


@router.get(
    "/customers/search",
    **OpenApiAgentMetadataBuilder.from_contract(
        "search_active_customers_for_portfolio",
        path="/pedidos-venda-abertos/customers/search",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def search_active_customers_for_portfolio_route(
    q: Optional[str] = Query(
        None,
        description="Busca por código, loja ou nome (vazio = primeira página de ativos).",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Clientes ativos no TOTVS (SA1) para amarração na carteira do vendedor."""
    try:
        result = build_search_active_customers_use_case().execute(
            SearchActiveCustomersRequest(query=q, page=page, page_size=page_size)
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="search_active_customers_for_portfolio",
            message="Clientes ativos carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar clientes ativos: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao buscar clientes ativos TOTVS: {exc}")
        return error_response(
            "Erro interno ao buscar clientes ativos.",
            status_code=500,
        )


@router.post(
    "/customers/enrichment",
    **OpenApiAgentMetadataBuilder.from_contract(
        "enrich_portfolio_customers",
        path="/pedidos-venda-abertos/customers/enrichment",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def enrich_portfolio_customers_route(body: EnrichCustomersBody = Body(...)):
    """Cidade/UF + faturamento 12m + última compra + flag de avatar (batch)."""
    try:
        pairs = [
            (item.customer_code, item.customer_store) for item in (body.customers or [])
        ]
        items = build_enrich_portfolio_customers_use_case().execute(
            EnrichCustomersRequest(customers=pairs)
        )
        return api_delpi_success(
            {"items": [item.to_dict() for item in items]},
            operation_id="enrich_portfolio_customers",
            message="Enriquecimento de clientes carregado.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao enriquecer clientes da carteira: {exc}")
        return error_response("Erro interno ao enriquecer clientes.", status_code=500)


@router.post(
    "/customers/open-order-metrics",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_customer_open_order_metrics",
        path="/pedidos-venda-abertos/customers/open-order-metrics",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_customer_open_order_metrics_route(
    body: OpenOrderMetricsBody = Body(default_factory=OpenOrderMetricsBody),
):
    """Agrega valor aberto e flag de atraso por cliente (pedidos em aberto)."""
    try:
        pairs = tuple(
            (item.customer_code, item.customer_store) for item in (body.customers or [])
        )
        items = build_list_customer_open_order_metrics_use_case().execute(
            ListCustomerOpenOrderMetricsRequest(customers=pairs)
        )
        return api_delpi_success(
            {"items": [item.to_dict() for item in items]},
            operation_id="list_customer_open_order_metrics",
            message="Métricas de pedidos em aberto por cliente carregadas.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao agregar métricas de pedidos em aberto: {exc}")
        return error_response(
            "Erro interno ao agregar métricas de pedidos em aberto.",
            status_code=500,
        )


@router.post(
    "/customers/billing-series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_customer_billing_series",
        path="/pedidos-venda-abertos/customers/billing-series",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_customer_billing_series_route(body: BillingSeriesBody = Body(...)):
    """Série de faturamento da carteira (período, granularidade e fallback months)."""
    try:
        pairs = [
            (item.customer_code, item.customer_store) for item in (body.customers or [])
        ]
        result = build_list_customer_billing_series_use_case().execute(
            ListCustomerBillingSeriesRequest(
                customers=pairs,
                months=body.months,
                start_date=body.start_date,
                end_date=body.end_date,
                granularity=body.granularity,
            )
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="list_customer_billing_series",
            message="Série de faturamento carregada.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar série de faturamento: {exc}")
        return error_response(
            "Erro interno ao carregar série de faturamento.",
            status_code=500,
        )


@router.get(
    "/customers/{codigo}/{loja}/avatar",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_customer_avatar",
        path="/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def get_customer_avatar_route(
    codigo: str = Path(..., min_length=1),
    loja: str = Path(..., min_length=1),
):
    try:
        avatar = build_manage_customer_avatar_use_case().get_file(
            customer_code=codigo,
            customer_store=loja,
        )
        return FileResponse(
            path=str(avatar.path),
            media_type=avatar.content_type or "application/octet-stream",
            filename=avatar.file_name,
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao obter avatar do cliente: {exc}")
        return error_response("Erro interno ao obter avatar.", status_code=500)


@router.put(
    "/customers/{codigo}/{loja}/avatar",
    **OpenApiAgentMetadataBuilder.from_contract(
        "upsert_customer_avatar",
        path="/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
async def upsert_customer_avatar_route(
    codigo: str = Path(..., min_length=1),
    loja: str = Path(..., min_length=1),
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        record = build_manage_customer_avatar_use_case().upsert(
            customer_code=codigo,
            customer_store=loja,
            original_name=file.filename or "avatar.bin",
            content=content,
            mime_type=file.content_type,
            uploaded_by_user_id=current_user_id(),
        )
        return api_delpi_success(
            {
                "customer_code": record.customer_code,
                "customer_store": record.customer_store,
                "content_type": record.content_type,
                "has_avatar": True,
                "avatar_url": (
                    f"/pedidos-venda-abertos/customers/"
                    f"{record.customer_code}/{record.customer_store}/avatar"
                ),
            },
            operation_id="upsert_customer_avatar",
            message="Logo do cliente salva.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao salvar avatar do cliente: {exc}")
        return error_response("Erro interno ao salvar avatar.", status_code=500)


@router.delete(
    "/customers/{codigo}/{loja}/avatar",
    **OpenApiAgentMetadataBuilder.from_contract(
        "delete_customer_avatar",
        path="/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def delete_customer_avatar_route(
    codigo: str = Path(..., min_length=1),
    loja: str = Path(..., min_length=1),
):
    try:
        build_manage_customer_avatar_use_case().delete(
            customer_code=codigo,
            customer_store=loja,
        )
        return api_delpi_success(
            {"has_avatar": False},
            operation_id="delete_customer_avatar",
            message="Logo do cliente removida.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao remover avatar do cliente: {exc}")
        return error_response("Erro interno ao remover avatar.", status_code=500)


@router.get(
    "/sellers/me",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_my_seller_portfolio",
        path="/pedidos-venda-abertos/sellers/me",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def get_my_seller_portfolio_route():
    try:
        portfolio = build_manage_seller_portfolio_use_case().get_me(current_user_id())
        return api_delpi_success(
            {
                "portfolio": portfolio_to_dict(portfolio) if portfolio else None,
                "is_admin": is_portfolio_admin(),
            },
            operation_id="get_my_seller_portfolio",
            message="Carteira do usuário carregada.",
        )
    except Exception as exc:
        log_error(f"Erro ao carregar carteira do usuário: {exc}")
        return error_response("Erro interno ao carregar carteira.", status_code=500)


@router.get(
    "/sellers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_seller_portfolios",
        path="/pedidos-venda-abertos/sellers",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def list_seller_portfolios_route(
    active_only: bool = Query(False, description="Se true, lista apenas ativos."),
):
    try:
        sellers = build_manage_seller_portfolio_use_case().list_sellers(
            active_only=active_only
        )
        return api_delpi_success(
            {"items": [portfolio_to_dict(item) for item in sellers]},
            operation_id="list_seller_portfolios",
            message="Vendedores carregados com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar vendedores: {exc}")
        return error_response("Erro interno ao listar vendedores.", status_code=500)


@router.post(
    "/sellers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "create_seller_portfolio",
        path="/pedidos-venda-abertos/sellers",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def create_seller_portfolio_route(body: CreateSellerBody = Body(...)):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        portfolio = build_manage_seller_portfolio_use_case().create_seller(
            CreateSellerRequest(
                user_id=body.user_id,
                display_name=body.display_name,
                created_by_user_id=current_user_id() or None,
                customers=tuple(customers),
            )
        )
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="create_seller_portfolio",
            message="Vendedor cadastrado com sucesso.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar vendedor: {exc}")
        return error_response("Erro interno ao cadastrar vendedor.", status_code=500)


@router.get(
    "/sellers/{seller_id}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_seller_portfolio",
        path="/pedidos-venda-abertos/sellers/{seller_id}",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def get_seller_portfolio_route(
    seller_id: str = Path(..., min_length=1),
):
    try:
        portfolio = build_manage_seller_portfolio_use_case().get_seller(seller_id)
        if portfolio is None:
            return error_response("Vendedor não encontrado.", status_code=404)
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="get_seller_portfolio",
            message="Vendedor carregado com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao carregar vendedor: {exc}")
        return error_response("Erro interno ao carregar vendedor.", status_code=500)


@router.patch(
    "/sellers/{seller_id}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "update_seller_portfolio",
        path="/pedidos-venda-abertos/sellers/{seller_id}",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def update_seller_portfolio_route(
    seller_id: str = Path(..., min_length=1),
    body: UpdateSellerBody = Body(...),
):
    try:
        portfolio = build_manage_seller_portfolio_use_case().update_seller(
            seller_id=seller_id,
            display_name=body.display_name,
            active=body.active,
        )
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="update_seller_portfolio",
            message="Vendedor atualizado com sucesso.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao atualizar vendedor: {exc}")
        return error_response("Erro interno ao atualizar vendedor.", status_code=500)


@router.delete(
    "/sellers/{seller_id}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "deactivate_seller_portfolio",
        path="/pedidos-venda-abertos/sellers/{seller_id}",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def deactivate_seller_portfolio_route(
    seller_id: str = Path(..., min_length=1),
):
    try:
        portfolio = build_manage_seller_portfolio_use_case().deactivate_seller(seller_id)
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="deactivate_seller_portfolio",
            message="Vendedor desativado com sucesso.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except Exception as exc:
        log_error(f"Erro ao desativar vendedor: {exc}")
        return error_response("Erro interno ao desativar vendedor.", status_code=500)


@router.put(
    "/sellers/{seller_id}/customers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "replace_seller_customers",
        path="/pedidos-venda-abertos/sellers/{seller_id}/customers",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def replace_seller_customers_route(
    seller_id: str = Path(..., min_length=1),
    body: ReplaceCustomersBody = Body(...),
):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        portfolio = build_manage_seller_portfolio_use_case().replace_customers(
            seller_id=seller_id,
            customers=customers,
        )
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="replace_seller_customers",
            message="Carteira de clientes atualizada.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao substituir clientes da carteira: {exc}")
        return error_response("Erro interno ao atualizar carteira.", status_code=500)


@router.post(
    "/sellers/{seller_id}/customers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "add_seller_customer",
        path="/pedidos-venda-abertos/sellers/{seller_id}/customers",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def add_seller_customer_route(
    seller_id: str = Path(..., min_length=1),
    body: SellerCustomerBody = Body(...),
):
    try:
        portfolio = build_manage_seller_portfolio_use_case().add_customer(
            seller_id=seller_id,
            customer=SellerCustomerAssignment(
                customer_code=body.customer_code.strip(),
                customer_store=body.customer_store.strip(),
                customer_name=(body.customer_name or "").strip() or None,
            ),
        )
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="add_seller_customer",
            message="Cliente adicionado à carteira.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao adicionar cliente: {exc}")
        return error_response("Erro interno ao adicionar cliente.", status_code=500)


@router.post(
    "/sellers/{seller_id}/customers/transfer",
    **OpenApiAgentMetadataBuilder.from_contract(
        "transfer_seller_customers",
        path="/pedidos-venda-abertos/sellers/{seller_id}/customers/transfer",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def transfer_seller_customers_route(
    seller_id: str = Path(..., min_length=1),
    body: TransferCustomersBody = Body(...),
):
    """Transfere clientes selecionados da carteira de origem para outro vendedor."""
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        source, target = build_manage_seller_portfolio_use_case().transfer_customers(
            source_seller_id=seller_id,
            target_seller_id=body.target_seller_id,
            customers=customers,
        )
        return api_delpi_success(
            {
                "source": portfolio_to_dict(source),
                "target": portfolio_to_dict(target),
                "transferred_count": len(customers),
            },
            operation_id="transfer_seller_customers",
            message="Clientes transferidos com sucesso.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao transferir clientes da carteira: {exc}")
        return error_response("Erro interno ao transferir clientes.", status_code=500)


@router.delete(
    "/sellers/{seller_id}/customers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "remove_seller_customer",
        path="/pedidos-venda-abertos/sellers/{seller_id}/customers",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)
def remove_seller_customer_route(
    seller_id: str = Path(..., min_length=1),
    customer_code: str = Query(..., min_length=1),
    customer_store: str = Query(..., min_length=1),
):
    try:
        portfolio = build_manage_seller_portfolio_use_case().remove_customer(
            seller_id=seller_id,
            customer_code=customer_code,
            customer_store=customer_store,
        )
        return api_delpi_success(
            portfolio_to_dict(portfolio),
            operation_id="remove_seller_customer",
            message="Cliente removido da carteira.",
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao remover cliente: {exc}")
        return error_response("Erro interno ao remover cliente.", status_code=500)


def _execute_outbound_invoices(
    *,
    customer_code: str,
    customer_store: str,
    start_date: Optional[str],
    end_date: Optional[str],
    page: int,
    page_size: int,
    situation: Optional[str],
    search: Optional[str],
    operation_id: str,
):
    use_case = build_list_customer_outbound_invoices_use_case()
    result = use_case.execute(
        ListCustomerOutboundInvoicesRequest(
            customer_code=customer_code,
            customer_store=customer_store,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            situation=situation,
            search=search,
        )
    )
    return api_delpi_success(
        result.to_dict(),
        operation_id=operation_id,
        message="Notas fiscais de saída do cliente carregadas com sucesso.",
    )


@router.get(
    "/totvs-outbound-invoices/{customer_code}/{customer_store}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_totvs_outbound_invoices",
        path="/pedidos-venda-abertos/totvs-outbound-invoices/{customer_code}/{customer_store}",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_totvs_outbound_invoices_route(
    customer_code: str = Path(
        ...,
        min_length=1,
        description="Customer code (A1_COD / D2_CLIENTE)",
    ),
    customer_store: str = Path(
        ...,
        min_length=1,
        description="Customer store (A1_LOJA / D2_LOJA)",
    ),
    start_date: Optional[str] = Query(
        None,
        description="Period start (YYYY-MM-DD). Default: last 90 days.",
    ),
    end_date: Optional[str] = Query(
        None,
        description="Period end (YYYY-MM-DD). Default: today.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    situation: Optional[str] = Query(
        "all",
        description="all | emitted | return. Soft-deleted cancelled invoices omitted.",
    ),
    search: Optional[str] = Query(
        None,
        description="Search by NF number, series, sales order, customer PO or product.",
    ),
):
    """
    Leitura TOTVS pura (sem membership PVA) — consumo BFF commercial-api.
    Reusa ListCustomerOutboundInvoicesUseCase. Não altera regras da rota legada NF.
    """
    try:
        return _execute_outbound_invoices(
            customer_code=customer_code,
            customer_store=customer_store,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            situation=situation,
            search=search,
            operation_id="list_totvs_outbound_invoices",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar NF TOTVS: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao listar NF TOTVS: {exc}")
        return error_response(
            "Erro interno ao carregar notas fiscais de saída do cliente (TOTVS).",
            status_code=500,
        )


@router.get(
    "/clientes/{codigo}/{loja}/notas-fiscais",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_cliente_notas_fiscais_saida",
        path="/pedidos-venda-abertos/clientes/{codigo}/{loja}/notas-fiscais",
    ),
)
@require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)
def list_cliente_notas_fiscais_saida_route(
    codigo: str = Path(..., min_length=1, description="Código do cliente (A1_COD / D2_CLIENTE)"),
    loja: str = Path(..., min_length=1, description="Loja do cliente (A1_LOJA / D2_LOJA)"),
    start_date: Optional[str] = Query(
        None,
        description="Início do período (AAAA-MM-DD). Default: últimos 90 dias.",
    ),
    end_date: Optional[str] = Query(
        None,
        description="Fim do período (AAAA-MM-DD). Default: hoje.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    situation: Optional[str] = Query(
        "all",
        description="all | emitted | return (devolução). Canceladas soft-deleted não retornam.",
    ),
    search: Optional[str] = Query(
        None,
        description="Busca por número NF, série, pedido de venda, pedido do cliente ou produto.",
    ),
):
    try:
        scope = _resolve_scope(None)
        allowed = build_resolve_portfolio_scope_use_case().customer_allowed(
            scope,
            customer_code=codigo,
            customer_store=loja,
        )
        if not allowed:
            return error_response(
                "Cliente fora da sua carteira.",
                status_code=404,
            )
        return _execute_outbound_invoices(
            customer_code=codigo,
            customer_store=loja,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            situation=situation,
            search=search,
            operation_id="list_cliente_notas_fiscais_saida",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar NF saída do cliente: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao listar NF saída do cliente: {exc}")
        return error_response(
            "Erro interno ao carregar notas fiscais de saída do cliente.",
            status_code=500,
        )
