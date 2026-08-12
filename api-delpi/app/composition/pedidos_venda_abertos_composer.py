from app.application.use_cases.pedidos_venda_abertos.enrich_portfolio_customers_use_case import (
    EnrichPortfolioCustomersUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case import (
    ListCustomerBillingSeriesUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_outbound_invoices_use_case import (
    ListCustomerOutboundInvoicesUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_customer_open_order_metrics_use_case import (
    ListCustomerOpenOrderMetricsUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_ops_abertas_use_case import (
    ListOpsAbertasUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.manage_customer_avatar_use_case import (
    ManageCustomerAvatarUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.manage_seller_portfolio_use_case import (
    ManageSellerPortfolioUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
    ResolvePortfolioScopeUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.search_active_customers_use_case import (
    SearchActiveCustomersUseCase,
)
from app.config import settings
from app.domain.ports.pedidos_venda_abertos.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from app.infrastructure.persistence.plugins.repositories.pedidos_venda_abertos.dual_read_seller_portfolio_repository import (
    DualReadSellerPortfolioRepository,
)
from app.infrastructure.persistence.plugins.repositories.pedidos_venda_abertos.postgres_commercial_seller_portfolio_repository import (
    PostgresCommercialSellerPortfolioRepository,
)
from app.infrastructure.persistence.plugins.repositories.pedidos_venda_abertos.postgres_customer_avatar_repository import (
    PostgresCustomerAvatarRepository,
)
from app.infrastructure.persistence.plugins.repositories.pedidos_venda_abertos.postgres_seller_portfolio_repository import (
    PostgresSellerPortfolioRepository,
)
from app.infrastructure.persistence.totvs.customer_repositories.customer_repository import (
    CustomerRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_enrichment_repository import (
    CustomerEnrichmentRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoices_repository import (
    CustomerOutboundInvoicesRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_query_repository import (
    OpsAbertasQueryRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.pedidos_venda_abertos_query_repository import (
    PedidosVendaAbertosQueryRepository,
)


def build_seller_portfolio_repository() -> SellerPortfolioRepositoryPort:
    """Dual-read commercial + legado; writes seguem COMMERCIAL_PORTFOLIO_SOURCE."""
    write_source = (settings.COMMERCIAL_PORTFOLIO_SOURCE or "commercial").strip().lower()
    return DualReadSellerPortfolioRepository(
        commercial=PostgresCommercialSellerPortfolioRepository(),
        legacy=PostgresSellerPortfolioRepository(),
        write_source=write_source,
    )


def build_manage_seller_portfolio_use_case() -> ManageSellerPortfolioUseCase:
    return ManageSellerPortfolioUseCase(repository=build_seller_portfolio_repository())


def build_resolve_portfolio_scope_use_case() -> ResolvePortfolioScopeUseCase:
    return ResolvePortfolioScopeUseCase(repository=build_seller_portfolio_repository())


def build_search_active_customers_use_case() -> SearchActiveCustomersUseCase:
    return SearchActiveCustomersUseCase(repository=CustomerRepository())


def build_manage_customer_avatar_use_case() -> ManageCustomerAvatarUseCase:
    return ManageCustomerAvatarUseCase(repository=PostgresCustomerAvatarRepository())


def build_enrich_portfolio_customers_use_case() -> EnrichPortfolioCustomersUseCase:
    return EnrichPortfolioCustomersUseCase(
        enrichment_repository=CustomerEnrichmentRepository(),
        avatar_use_case=build_manage_customer_avatar_use_case(),
    )


def build_list_customer_billing_series_use_case() -> ListCustomerBillingSeriesUseCase:
    return ListCustomerBillingSeriesUseCase(
        enrichment_repository=CustomerEnrichmentRepository(),
    )


def build_list_pedidos_venda_abertos_use_case() -> ListPedidosVendaAbertosUseCase:
    return ListPedidosVendaAbertosUseCase(
        repository=PedidosVendaAbertosQueryRepository(),
    )


def build_list_customer_open_order_metrics_use_case() -> ListCustomerOpenOrderMetricsUseCase:
    return ListCustomerOpenOrderMetricsUseCase(
        repository=PedidosVendaAbertosQueryRepository(),
    )


def build_list_ops_abertas_use_case() -> ListOpsAbertasUseCase:
    return ListOpsAbertasUseCase(
        repository=OpsAbertasQueryRepository(),
    )


def build_list_customer_outbound_invoices_use_case() -> ListCustomerOutboundInvoicesUseCase:
    return ListCustomerOutboundInvoicesUseCase(
        repository=CustomerOutboundInvoicesRepository(),
    )
