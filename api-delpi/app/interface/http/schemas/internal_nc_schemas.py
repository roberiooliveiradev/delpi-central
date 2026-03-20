# app/interface/http/schemas/internal_nc_schemas.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateInternalNonconformityBody(BaseModel):
    source_type: str
    detected_by_user_id: str
    detection_date: date
    item_code: str
    item_description: str
    sector: str
    defect_category: str
    defect_description: str
    severity: str
    priority: str

    source_inspection_id: Optional[str] = None
    production_order: Optional[str] = None
    lot_number: Optional[str] = None
    operation_code: Optional[str] = None
    operation_description: Optional[str] = None
    defective_quantity: Decimal = Decimal("0")
    inspected_quantity: Optional[Decimal] = None
    containment_action_summary: Optional[str] = None
    disposition_type: Optional[str] = None
    immediate_cause_notes: Optional[str] = None
    root_cause_summary: Optional[str] = None
    responsible_user_id: Optional[str] = None
    due_date: Optional[date] = None


class UpdateInternalNonconformityBody(BaseModel):
    source_type: str
    detected_by_user_id: str
    detection_date: date
    item_code: str
    item_description: str
    sector: str
    defect_category: str
    defect_description: str
    severity: str
    priority: str
    current_status: str

    source_inspection_id: Optional[str] = None
    production_order: Optional[str] = None
    lot_number: Optional[str] = None
    operation_code: Optional[str] = None
    operation_description: Optional[str] = None
    defective_quantity: Decimal = Decimal("0")
    inspected_quantity: Optional[Decimal] = None
    containment_action_summary: Optional[str] = None
    disposition_type: Optional[str] = None
    immediate_cause_notes: Optional[str] = None
    root_cause_summary: Optional[str] = None
    responsible_user_id: Optional[str] = None
    due_date: Optional[date] = None
    cancellation_reason: Optional[str] = None


class InternalNonconformityResponse(BaseModel):
    id: str
    code: str
    source_type: str
    source_inspection_id: Optional[str]
    production_order: Optional[str]
    item_code: str
    item_description: str
    lot_number: Optional[str]
    sector: str
    operation_code: Optional[str]
    operation_description: Optional[str]
    defect_category: str
    defect_description: str
    detected_by_user_id: str
    detection_date: date
    defective_quantity: Decimal
    inspected_quantity: Optional[Decimal]
    severity: str
    priority: str
    current_status: str
    containment_action_summary: Optional[str]
    disposition_type: Optional[str]
    immediate_cause_notes: Optional[str]
    root_cause_summary: Optional[str]
    responsible_user_id: Optional[str]
    due_date: Optional[date]
    closed_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaginatedInternalNonconformityResponse(BaseModel):
    items: list[InternalNonconformityResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class ListInternalNonconformitiesQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    current_status: Optional[str] = None
    sector: Optional[str] = None
    search: Optional[str] = None


class TransitionInternalNonconformityStatusBody(BaseModel):
    target_status: str
    actor_user_id: str
    justification: Optional[str] = None

class AddInternalNcRootCauseBody(BaseModel):
    analysis_method: Optional[str] = None
    cause_dimension: Optional[str] = None
    category: Optional[str] = None
    why_level: Optional[int] = None
    description: str
    is_root_cause: bool = False
    created_by_user_id: str


class InternalNcRootCauseResponse(BaseModel):
    id: str
    nonconformity_id: str
    analysis_method: Optional[str]
    cause_dimension: Optional[str]
    category: Optional[str]
    why_level: Optional[int]
    description: str
    is_root_cause: bool
    created_by_user_id: str
    created_at: datetime