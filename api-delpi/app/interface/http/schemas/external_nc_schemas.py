# app/interface/http/schemas/external_nc_schemas.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateExternalNonconformityBody(BaseModel):
    company_unit: str
    supplier_id: str
    supplier_name_snapshot: str
    opened_by_user_id: str
    occurrence_date: date
    detection_date: date
    severity: str
    priority: str
    title: str
    problem_description: str

    customer_name: Optional[str] = None
    origin_type: str = "supplier"
    source_channel: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    material_specification: Optional[str] = None
    lot_number: Optional[str] = None
    purchase_order: Optional[str] = None
    invoice_number: Optional[str] = None
    document_reference: Optional[str] = None
    defective_quantity: Decimal = Decimal("0")
    inspected_quantity: Optional[Decimal] = None
    uom: Optional[str] = None
    occurrence_type: Optional[str] = None
    defect_category: Optional[str] = None
    recurrence_flag: bool = False
    containment_required: bool = False
    business_impact: Optional[str] = None
    customer_impact: Optional[str] = None
    production_impact: Optional[str] = None
    cost_estimate: Optional[Decimal] = None
    responsible_user_id: Optional[str] = None
    due_date: Optional[date] = None


class UpdateExternalNonconformityBody(BaseModel):
    company_unit: str
    supplier_id: str
    supplier_name_snapshot: str
    occurrence_date: date
    detection_date: date
    severity: str
    priority: str
    title: str
    problem_description: str

    customer_name: Optional[str] = None
    origin_type: str = "supplier"
    source_channel: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    material_specification: Optional[str] = None
    lot_number: Optional[str] = None
    purchase_order: Optional[str] = None
    invoice_number: Optional[str] = None
    document_reference: Optional[str] = None
    defective_quantity: Decimal = Decimal("0")
    inspected_quantity: Optional[Decimal] = None
    uom: Optional[str] = None
    occurrence_type: Optional[str] = None
    defect_category: Optional[str] = None
    recurrence_flag: bool = False
    containment_required: bool = False
    business_impact: Optional[str] = None
    customer_impact: Optional[str] = None
    production_impact: Optional[str] = None
    cost_estimate: Optional[Decimal] = None
    current_status: str = "draft"
    supplier_status: str = "not-requested"
    responsible_user_id: Optional[str] = None
    due_date: Optional[date] = None
    cancellation_reason: Optional[str] = None


class ListExternalNonconformitiesQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    current_status: Optional[str] = None
    supplier_id: Optional[str] = None
    search: Optional[str] = None


class ExternalNonconformityResponse(BaseModel):
    id: str
    code: str
    company_unit: str
    supplier_id: str
    supplier_name_snapshot: str
    customer_name: Optional[str]
    origin_type: str
    source_channel: Optional[str]
    material_code: Optional[str]
    material_description: Optional[str]
    material_specification: Optional[str]
    lot_number: Optional[str]
    purchase_order: Optional[str]
    invoice_number: Optional[str]
    document_reference: Optional[str]
    occurrence_date: date
    detection_date: date
    defective_quantity: Decimal
    inspected_quantity: Optional[Decimal]
    uom: Optional[str]
    severity: str
    priority: str
    occurrence_type: Optional[str]
    defect_category: Optional[str]
    recurrence_flag: bool
    containment_required: bool
    title: str
    problem_description: str
    business_impact: Optional[str]
    customer_impact: Optional[str]
    production_impact: Optional[str]
    cost_estimate: Optional[Decimal]
    current_status: str
    supplier_status: str
    responsible_user_id: Optional[str]
    opened_by_user_id: str
    due_date: Optional[date]
    closed_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaginatedExternalNonconformityResponse(BaseModel):
    items: list[ExternalNonconformityResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

class TransitionExternalNonconformityStatusBody(BaseModel):
    target_status: str
    actor_user_id: str
    justification: Optional[str] = None
    effectiveness_approved: bool = False


class AddExternalNcCommentBody(BaseModel):
    comment_type: str = "general"
    content: str
    is_internal: bool = True
    created_by_user_id: str


class ExternalNcCommentResponse(BaseModel):
    id: str
    nc_type: str
    nc_id: str
    comment_type: str
    content: str
    is_internal: bool
    created_by_user_id: str
    created_at: datetime


class UploadExternalNcAttachmentBody(BaseModel):
    file_name: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str] = None
    uploaded_by_user_id: str


class ExternalNcAttachmentResponse(BaseModel):
    id: str
    nc_type: Optional[str]
    nc_id: Optional[str]
    action_id: Optional[str]
    effectiveness_check_id: Optional[str]
    file_name: str
    original_name: str
    mime_type: Optional[str]
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str]
    uploaded_by_user_id: str
    uploaded_at: datetime