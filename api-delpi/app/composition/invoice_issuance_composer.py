"""Composition root — invoice-issuance."""
from __future__ import annotations

from app.application.use_cases.invoice_issuance.invoice_issuance_use_cases import (
    CancelInvoiceIssuanceRequestUseCase,
    CreateInvoiceIssuanceRequestUseCase,
    GetInvoiceIssuanceRequestUseCase,
    GetWarehouse01BalanceUseCase,
    IssueInvoiceIssuanceRequestUseCase,
    ListInvoiceIssuanceOpenSalesOrdersUseCase,
    ListInvoiceIssuanceRequestsUseCase,
    ResubmitInvoiceIssuanceRequestUseCase,
    ReturnInvoiceIssuanceRequestUseCase,
    SearchIssuanceCarriersUseCase,
    SearchIssuanceProductsUseCase,
    SearchPartiesUseCase,
    StartInvoiceIssuanceRequestUseCase,
    UpdateReturnedInvoiceIssuanceRequestUseCase,
)
from app.infrastructure.persistence.plugins.repositories.invoice_issuance.postgres_invoice_issuance_repository import (
    PostgresInvoiceIssuanceRepository,
)
from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)
from app.infrastructure.persistence.totvs.invoice_issuance_repositories.totvs_invoice_issuance_lookup_repository import (
    TotvsInvoiceIssuanceLookupRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.pedidos_venda_abertos_query_repository import (
    PedidosVendaAbertosQueryRepository,
)
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_repository import (
    TotvsSupplierRepository,
)


def build_requests_repository() -> PostgresInvoiceIssuanceRepository:
    return PostgresInvoiceIssuanceRepository()


def build_lookups() -> TotvsInvoiceIssuanceLookupRepository:
    return TotvsInvoiceIssuanceLookupRepository()


def build_suppliers() -> TotvsSupplierRepository:
    return TotvsSupplierRepository()


def build_search_parties_use_case() -> SearchPartiesUseCase:
    return SearchPartiesUseCase(build_lookups(), build_suppliers())


def build_search_products_use_case() -> SearchIssuanceProductsUseCase:
    return SearchIssuanceProductsUseCase(build_lookups())


def build_search_carriers_use_case() -> SearchIssuanceCarriersUseCase:
    return SearchIssuanceCarriersUseCase(build_lookups())


def build_warehouse_balance_use_case() -> GetWarehouse01BalanceUseCase:
    return GetWarehouse01BalanceUseCase(build_lookups())


def build_open_sales_orders_use_case() -> ListInvoiceIssuanceOpenSalesOrdersUseCase:
    return ListInvoiceIssuanceOpenSalesOrdersUseCase(
        ListPedidosVendaAbertosUseCase(PedidosVendaAbertosQueryRepository())
    )


def build_create_use_case() -> CreateInvoiceIssuanceRequestUseCase:
    return CreateInvoiceIssuanceRequestUseCase(
        build_requests_repository(), build_lookups(), build_suppliers()
    )


def build_list_use_case() -> ListInvoiceIssuanceRequestsUseCase:
    return ListInvoiceIssuanceRequestsUseCase(build_requests_repository())


def build_get_use_case() -> GetInvoiceIssuanceRequestUseCase:
    return GetInvoiceIssuanceRequestUseCase(
        build_requests_repository(), build_lookups()
    )


def build_update_returned_use_case() -> UpdateReturnedInvoiceIssuanceRequestUseCase:
    return UpdateReturnedInvoiceIssuanceRequestUseCase(
        build_requests_repository(), build_lookups(), build_suppliers()
    )


def build_resubmit_use_case() -> ResubmitInvoiceIssuanceRequestUseCase:
    return ResubmitInvoiceIssuanceRequestUseCase(build_requests_repository())


def build_start_use_case() -> StartInvoiceIssuanceRequestUseCase:
    return StartInvoiceIssuanceRequestUseCase(build_requests_repository())


def build_return_use_case() -> ReturnInvoiceIssuanceRequestUseCase:
    return ReturnInvoiceIssuanceRequestUseCase(build_requests_repository())


def build_issue_use_case() -> IssueInvoiceIssuanceRequestUseCase:
    return IssueInvoiceIssuanceRequestUseCase(build_requests_repository())


def build_cancel_use_case() -> CancelInvoiceIssuanceRequestUseCase:
    return CancelInvoiceIssuanceRequestUseCase(build_requests_repository())
