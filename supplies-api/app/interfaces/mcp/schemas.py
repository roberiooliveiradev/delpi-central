"""SURI MCP typed parameter models (semantic contract freeze rev.3).

Each capability gets an explicit pydantic model so the wire schema is
closed (``additionalProperties: false``) — unknown fields are rejected
by the SDK argument validation AND by the semantic dispatcher in depth.
New entities/analyses add their own models via contract + owner, never
a generic dict.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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
