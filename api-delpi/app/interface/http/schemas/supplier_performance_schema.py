"""Read-only IDF contract; absent evidence is never a zero or an assumed 100."""

from typing import Literal

from pydantic import BaseModel, Field


class PerformanceComponent(BaseModel):
    assessed_count: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    unknown_count: int = Field(ge=0)
    conditional_count: int = Field(ge=0)
    urgent_count: int = Field(ge=0)
    index: float | None = Field(ge=0, le=100)


class SupplierPerformanceItem(BaseModel):
    supplier_code: str
    supplier_store: str
    supplier_name: str
    branches: list[str]
    quality: PerformanceComponent
    delivery: PerformanceComponent
    idf: float | None = Field(ge=0, le=100)
    quality_contribution: float | None
    delivery_contribution: float | None
    status: Literal["complete", "inconsistent", "missing_quality", "missing_delivery"]


class PerformanceSummary(BaseModel):
    suppliers: int
    evaluated: int
    incomplete: int
    average_idf: float | None
    average_quality: float | None
    average_delivery: float | None
    inspection_count: int
    receipt_count: int


class PerformanceMethodology(BaseModel):
    quality_weight: Literal[70]
    delivery_weight: Literal[30]
    scale: Literal[100]
    quality: Literal["approved_inspections_over_concluded"]
    quality_date: Literal["report_date"]
    delivery: Literal["on_time_receipt_lines_over_receipt_lines"]
    delivery_date: Literal["receipt_entry_date"]
    product_scope: Literal["supplies_otd"]
    classification_bands: None
    quality_includes_conditional_and_urgent: Literal[True]


class PerformancePeriod(BaseModel):
    # Keys match the shared Portal period contract.
    from_date: str = Field(alias="from")
    to: str


class SupplierPerformancePayload(BaseModel):
    items: list[SupplierPerformanceItem]
    summary: PerformanceSummary
    methodology: PerformanceMethodology
    period: PerformancePeriod
    branches: list[str]
    calculated_at: str


class SupplierPerformanceResponse(BaseModel):
    success: bool
    message: str
    data: SupplierPerformancePayload
    error: dict | None = None
    meta: dict


class SupplierPerformanceExportPayload(SupplierPerformancePayload):
    """Fresh detail rows in their own grains, not a fabricated PO↔inspection join."""
    inspections: list[dict]
    deliveries: list[dict]
    supplier_selected: dict[str, str] | None = None


class SupplierPerformanceExportResponse(BaseModel):
    success: bool
    message: str
    data: SupplierPerformanceExportPayload
    error: dict | None = None
    meta: dict
