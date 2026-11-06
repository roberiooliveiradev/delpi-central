"""SURI MCP typed parameter models (semantic contract freeze rev.3).

Each capability gets an explicit pydantic model so the wire schema is
closed (``additionalProperties: false``) — unknown fields are rejected
by the SDK argument validation AND by the semantic dispatcher in depth.
New entities/analyses add their own models via contract + owner, never
a generic dict.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.safety_stock_service import (
    ALLOWED_SORT_DIRECTIONS,
    ALLOWED_SORT_FIELDS,
    ALLOWED_STATUSES,
    BRANCH_SCOPES,
)
from app.interfaces.mcp.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SAMPLE_SIZE,
)


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PurchaseOrderSearchFilters(_ClosedModel):
    """Closed filter vocabulary for ``read(entity=purchase_orders,
    action=search)`` — parity with the BFF list contract."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    order_number: str | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    expected_delivery_from: str | None = None
    expected_delivery_to: str | None = None
    late_only: bool = False
    sort_by: str | None = None
    sort_dir: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1)


class PurchaseOrderAnalyzeFilters(_ClosedModel):
    """Closed filter vocabulary for
    ``analyze(analysis=purchase_orders_summary)``."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    order_number: str | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    expected_delivery_from: str | None = None
    expected_delivery_to: str | None = None
    late_only: bool = False


class PurchaseOrderIdentity(_ClosedModel):
    """Identity for ``read(entity=purchase_orders, action=get)``."""

    branch: str
    order_number: str


class PurchaseOrderExportFilters(_ClosedModel):
    """Filters for ``read(entity=purchase_orders, action=export)`` —
    same closed vocabulary as search, without pagination."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    order_number: str | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    expected_delivery_from: str | None = None
    expected_delivery_to: str | None = None
    late_only: bool = False
    sort_by: str | None = None
    sort_dir: str | None = None


class PurchaseRequestSearchFilters(_ClosedModel):
    """Closed filter vocabulary for ``read(entity=purchase_requests,
    action=search)`` — parity with the purchase-requests-api list
    contract consumed by the BFF."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    date_from: str | None = None
    date_to: str | None = None
    request_number: str | None = None
    requester_user_id: list[str] | None = None
    cost_center: list[str] | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    order_number: str | None = None
    overall_stage: list[str] | None = None
    sort_by: str | None = None
    sort_dir: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1)


class PurchaseRequestSummaryFilters(_ClosedModel):
    """Filters for ``read(entity=purchase_requests, action=summary)`` —
    same filter set as search minus sort and pagination."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    date_from: str | None = None
    date_to: str | None = None
    request_number: str | None = None
    requester_user_id: list[str] | None = None
    cost_center: list[str] | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    order_number: str | None = None
    overall_stage: list[str] | None = None


class PurchaseRequestRequestersFilters(_ClosedModel):
    """Filters for ``read(entity=purchase_requests, action=requesters)``
    — PR-api requesters facet contract (no requester_user_id or
    overall_stage keys upstream)."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    date_from: str | None = None
    date_to: str | None = None
    request_number: str | None = None
    cost_center: list[str] | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    order_number: str | None = None


class PurchaseRequestCostCentersFilters(_ClosedModel):
    """Filters for ``read(entity=purchase_requests, action=cost_centers)``
    — PR-api cost-centers facet contract (no cost_center key upstream)."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    date_from: str | None = None
    date_to: str | None = None
    request_number: str | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    order_number: str | None = None


class PurchaseRequestIdentity(_ClosedModel):
    """Identity for ``read(entity=purchase_requests, action=get)`` —
    unequivocal ``{branch, request_number}`` (BFF path contract)."""

    branch: str
    request_number: str


class PurchaseRequestDetailFilters(_ClosedModel):
    """Optional context filters for ``read(entity=purchase_requests,
    action=get)`` — the PR-api detail endpoint accepts a facet-scoped
    lookup context alongside the path identity."""

    date_from: str | None = None
    date_to: str | None = None
    cost_center: list[str] | None = None


class PurchaseRequestExportFilters(_ClosedModel):
    """Filters for ``read(entity=purchase_requests, action=export)`` —
    same closed vocabulary as search, without pagination."""

    branch: list[str] = Field(
        description="Unidades operacionais obrigatórias (ex.: ['01'])."
    )
    date_from: str | None = None
    date_to: str | None = None
    request_number: str | None = None
    requester_user_id: list[str] | None = None
    cost_center: list[str] | None = None
    product_code: str | None = None
    supplier_code: str | None = None
    order_number: str | None = None
    overall_stage: list[str] | None = None
    sort_by: str | None = None
    sort_dir: str | None = None


class SupplierSearchFilters(_ClosedModel):
    """Filters for ``read(entity=suppliers, action=search)`` — parity
    with the BFF paged SA2 search contract."""

    query: str | None = None
    state: str | None = None
    blocked: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1)
    sort_by: str | None = None
    sort_dir: str | None = None


class SupplierIdentity(_ClosedModel):
    """Identity for ``read(entity=suppliers, action=get)`` — ficha 360."""

    supplier_code: str = Field(
        description="Código do fornecedor (até 6 dígitos)."
    )
    supplier_store: str = Field(
        description="Loja do fornecedor (até 2 dígitos)."
    )


class SupplierCatalogFilters(_ClosedModel):
    """Filters for ``read(entity=suppliers, action=catalogs)`` —
    ``kind`` belongs to the closed catalog allowlist."""

    kind: str = Field(
        description=(
            "Catálogo TOTVS da allowlist (ex.: states, countries, "
            "payment-conditions, payment-methods, financial-natures, "
            "municipalities, carriers, segments)."
        )
    )
    query: str | None = None
    state: str | None = None
    code: str | None = None
    limit: int | None = Field(default=None, ge=1)


class SupplierTaxIdFilters(_ClosedModel):
    """Filters for ``read(entity=suppliers, action=search_by_tax_id |
    existing)`` — exact CNPJ duplicate lookups."""

    tax_id: str = Field(
        description="CNPJ com ou sem máscara — validado como CNPJ real."
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1)


class SupplierOperationIdentity(_ClosedModel):
    """Identity for ``read(entity=suppliers, action=operations)`` —
    tracked write status via the api-delpi operation record."""

    operation_id: str


class PostalCodeIdentity(_ClosedModel):
    """Identity for ``read(entity=postal_codes, action=lookup)`` —
    address proposal by CEP (proposal only, never persists)."""

    postal_code: str = Field(description="CEP com ou sem máscara (8 dígitos).")


class SupplierPreviewFilters(_ClosedModel):
    """Filters for ``analyze(analysis=supplier_creation_preview)`` —
    registry-assisted pre-registration preview (read-only)."""

    tax_id: str = Field(
        description="CNPJ com ou sem máscara — validado como CNPJ real."
    )


DEFAULT_ANALYZE_SAMPLE_SIZE = DEFAULT_SAMPLE_SIZE


class SupplierWriteOperation(_ClosedModel):
    """One governed write operation for ``execute(entity=suppliers)``.

    ``action=create`` requires ``supplier`` (cadastral payload — closed
    allowlist enforced against the canonical BFF contract, not a parallel
    schema) and forbids identity/``fields``. ``action=update`` requires
    ``supplier_code`` + ``supplier_store`` (unequivocal identity) plus
    ``fields`` and forbids ``supplier``. ``idempotency_key`` binds client
    retries to a single execution attempt.
    """

    idempotency_key: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Chave opcional de idempotência por operação — repetições com "
            "a mesma chave e mesmo payload retornam o resultado anterior "
            "sem reexecutar a escrita."
        ),
    )
    supplier_code: str | None = Field(
        default=None,
        description="Código do fornecedor (update — até 6 dígitos).",
    )
    supplier_store: str | None = Field(
        default=None,
        description="Loja do fornecedor (update — até 2 dígitos).",
    )
    supplier: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Payload cadastral para action=create — mesmos campos do "
            "Portal (ex.: tax_id, supplier_name, supplier_short_name, "
            "person_type, address, postal_code, state, city, "
            "payment_condition_code, payment_method_code, "
            "financial_nature_code, accounting_account, country_code, "
            "bacen_country_code, rohs_indicator, supplier_store)."
        ),
    )
    fields: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Campos editáveis para action=update — allowlist homologada "
            "do Portal (ex.: phone, email, contact_name, address). Campos "
            "de identidade/documento (tax_id, supplier_code, "
            "supplier_store) são imutáveis e rejeitados."
        ),
    )

class DeliveriesLateFilters(_ClosedModel):
    """read(deliveries,late) — mirrors GET /deliveries/late."""

    branch: list[str] | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    sort_by: str | None = None
    sort_dir: str | None = None
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=1000)


class InventorySummaryFilters(_ClosedModel):
    """read(inventory,summary) — mirrors /stock-balances/summary."""

    branch: list[str] | None = None
    warehouse: str | None = None


class InventoryItemsFilters(_ClosedModel):
    """read(inventory,items) — mirrors /stock-balances/items."""

    branch: list[str] | None = None
    warehouse: str | None = None
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=500)
    sort: str | None = None

# Closed safety_stock vocabularies — derived from the BFF contract owner
# (safety_stock_service) so the wire schema stays a projection of the
# canonical allowlists, never a second hardcoded list.
SafetyStockStatus = Literal[*sorted(ALLOWED_STATUSES)]
SafetyStockBranchScope = Literal[*sorted(BRANCH_SCOPES)]
SafetyStockBranch = Literal[*sorted(OPERATIONAL_UNITS)]
SafetyStockSortField = Literal[*sorted(ALLOWED_SORT_FIELDS)]
SafetyStockSortDirection = Literal[*sorted(ALLOWED_SORT_DIRECTIONS)]


class SafetyStockScopeFilters(_ClosedModel):
    """read(safety_stock,filters)."""
    branch: SafetyStockBranchScope | None = None
    includeBlocked: bool | None = None


class SafetyStockSummaryFilters(_ClosedModel):
    """read(safety_stock,summary)."""
    branch: SafetyStockBranchScope | None = None
    includeBlocked: bool | None = None
    productGroup: str | None = None
    unit: str | None = None
    search: str | None = None
    status: SafetyStockStatus | None = None
    includeWithoutSafetyStock: bool | None = None


class SafetyStockItemsFilters(SafetyStockSummaryFilters):
    """read(safety_stock,items)."""
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=200)
    sortBy: SafetyStockSortField | None = None
    sortDirection: SafetyStockSortDirection | None = None


class SafetyStockItemIdentity(_ClosedModel):
    """read(safety_stock,details|suppliers)."""
    code: str = Field(min_length=1)
    branch: SafetyStockBranch | None = None

class OtdAggregateFilters(_ClosedModel):
    """read(otd,aggregate) — GET /analytics/otd."""
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class OtdSeriesFilters(_ClosedModel):
    """read(otd,series) — GET /analytics/otd/series."""
    branch: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    granularity: str | None = None


class OverviewSummaryFilters(_ClosedModel):
    """analyze(overview_summary) — GET /analytics/overview."""
    branch: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None

class ConsumptionSearchFilters(_ClosedModel):
    """read(consumption,search) — GET /consumption-audit/orders."""
    unit: str
    search: str | None = None
    product: str | None = None
    date_type: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    status: str | None = None
    work_center: str | None = None
    operation: str | None = None
    page: int | None = Field(default=None, ge=1, le=10000)
    page_size: int | None = Field(default=None, ge=1, le=50)


class ConsumptionComparisonFilters(_ClosedModel):
    """read(consumption,comparison) — /consumption-audit/comparison."""
    unit: str
    orders: list[str] = Field(min_length=2, max_length=10)


class ConsumptionIdentity(_ClosedModel):
    """read(consumption,get) — /consumption-audit/orders/{op}."""
    unit: str
    production_order: str = Field(min_length=11, max_length=11)

class MarketCommonFilters(_ClosedModel):
    instrument: str | None = None
    currency: str | None = None
    fx_kind: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class MarketSeriesFilters(MarketCommonFilters):
    granularity: str | None = None


class MarketImportSeriesFilters(_ClosedModel):
    ncm: str | None = None
    granularity: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    country_code: str | None = None
    state_code: str | None = None


class MarketProducerPriceFilters(_ClosedModel):
    series_id: str | None = None
    granularity: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class MarketFxFilters(_ClosedModel):
    fx_kind: str | None = None
    granularity: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class MarketQuoteFilters(_ClosedModel):
    instruments: str | None = None
    granularity: str | None = None
    currency: str | None = None
    fx_kind: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class MarketMonthlyFilters(MarketCommonFilters):
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1)


class ComexProductsFilters(_ClosedModel):
    code: str | None = None
    description: str | None = None
    product_type: str | None = None
    group_code: str | None = None
    search: str | None = None
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1)


class ComexNcmListFilters(_ClosedModel):
    status: str | None = None


class ComexIdentity(_ClosedModel):
    """identity for ncm_governance_get / view_get."""
    governance_id: str | None = None
    view_id: str | None = None

class EmptyFilters(_ClosedModel):
    """no-op filter object for actions that take no filters."""


class UsersRelatedFilters(_ClosedModel):
    """read(users,related_requests)."""
    branch: list[str] | None = None
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=50)
    sort_by: str | None = None
    sort_dir: str | None = None


class UsersIdentity(_ClosedModel):
    """identity {user_id} for profile/photo/related_requests."""
    user_id: str = Field(min_length=1)

class ComexWriteOperation(_ClosedModel):
    """One governed write operation for ``execute(entity=comex)``.

    Key sets are enforced per action in the dispatcher — this model only
    declares the closed union vocabulary: NCM request/transition and view
    create/update fields plus ``idempotency_key``.
    """
    idempotency_key: str | None = Field(default=None, max_length=128)
    ncm_code: str | None = None
    description: str | None = None
    ncm_version: str | None = None
    family_code: str | None = None
    product_codes: list[str] | None = None
    notes: str | None = None
    initial_status: str | None = None
    governance_id: str | None = None
    to_status: str | None = None
    expected_revision: int | None = None
    view_id: str | None = None
    name: str | None = None
    unit_scope: str | None = None
    selected_product_codes: list[str] | None = None
    selected_materials: list[str] | None = None
    approved_ncm_references: list[str] | None = None
    selected_metrics: list[str] | None = None
    date_range: dict | None = None
    granularity: str | None = None
    view_mode: str | None = None

class EnrichmentWriteOperation(_ClosedModel):
    """One governed write operation for ``execute(entity=enrichment)``.

    Per-action key sets are enforced in the dispatcher — this model only
    declares the closed union vocabulary for review/decision/prepare
    writes plus ``idempotency_key``.
    """
    idempotency_key: str | None = Field(default=None, max_length=128)
    supplier_code: str | None = None
    supplier_store: str | None = None
    review_id: str | None = None
    field_key: str | None = None
    field_keys: list[str] | None = None
    decision: str | None = None
    expected_revision: int | None = None
    reason_code: str | None = None

class PersonalWriteOperation(_ClosedModel):
    """One governed write operation for ``execute`` on session/users.

    Per-action key sets enforced in the dispatcher — this model only
    declares the closed union vocabulary for preferences/profile updates
    plus ``idempotency_key``.
    """
    idempotency_key: str | None = Field(default=None, max_length=128)
    user_id: str | None = None
    defaultBranch: str | None = None
    tableDensity: str | None = None
    preferences: dict | None = None

class ComexDeleteOperation(_ClosedModel):
    """execute(comex,view_delete) — confirmation-required destructive op.

    ``confirmation`` must repeat the exact target: the service will not
    run unless ``confirmation.view_id`` equals ``view_id`` and
    ``confirmation.acknowledged`` is true.
    """
    idempotency_key: str | None = Field(default=None, max_length=128)
    view_id: str = Field(min_length=1)
    confirmation: dict | None = None

class ProcurementDiagnosticFilters(_ClosedModel):
    """analyze(procurement_diagnostic) — multi-entity read-only compose."""
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    include_sections: list[str] | None = None

