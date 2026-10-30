"""SURI MCP typed parameter models (semantic contract freeze rev.2).

Each capability gets an explicit pydantic model so the wire schema is
closed (``additionalProperties: false``) — unknown fields are rejected
by the SDK argument validation AND by the semantic dispatcher in depth.
New entities/analyses add their own models via contract + owner, never
a generic dict.
"""

from __future__ import annotations

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


DEFAULT_ANALYZE_SAMPLE_SIZE = DEFAULT_SAMPLE_SIZE
