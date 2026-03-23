# app/interface/http/schemas/internal_nc_schemas.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any

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


class CreateInternalNcActionBody(BaseModel):
    root_cause_id: Optional[str] = None
    action_type: str
    title: str
    description: str
    responsible_user_id: Optional[str] = None
    responsible_external_name: Optional[str] = None
    responsible_external_email: Optional[str] = None
    start_date: Optional[date] = None
    due_date: date
    verification_required: bool = False
    effectiveness_due_date: Optional[date] = None
    created_by_user_id: str


class UpdateInternalNcActionBody(BaseModel):
    root_cause_id: Optional[str] = None
    action_type: str
    title: str
    description: str
    responsible_user_id: Optional[str] = None
    responsible_external_name: Optional[str] = None
    responsible_external_email: Optional[str] = None
    start_date: Optional[date] = None
    due_date: date
    verification_required: bool = False
    effectiveness_due_date: Optional[date] = None


class CompleteInternalNcActionBody(BaseModel):
    actor_user_id: str
    completion_notes: Optional[str] = None


class InternalNcActionResponse(BaseModel):
    id: str
    nonconformity_id: str
    root_cause_id: Optional[str]
    action_type: str
    title: str
    description: str
    responsible_user_id: Optional[str]
    responsible_external_name: Optional[str]
    responsible_external_email: Optional[str]
    start_date: Optional[date]
    due_date: date
    completed_at: Optional[datetime]
    status: str
    verification_required: bool
    effectiveness_due_date: Optional[date]
    completion_notes: Optional[str]
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime


class RegisterInternalNcEffectivenessCheckBody(BaseModel):
    action_id: Optional[str] = None
    checked_by_user_id: str
    checked_at: datetime
    criteria: str
    result: str
    notes: Optional[str] = None
    next_action: Optional[str] = None


class InternalNcEffectivenessCheckResponse(BaseModel):
    id: str
    nonconformity_id: str
    action_id: Optional[str]
    checked_by_user_id: str
    checked_at: datetime
    criteria: str
    result: str
    notes: Optional[str]
    next_action: Optional[str]
    created_at: datetime


class AddInternalNcTeamMemberBody(BaseModel):
    user_id: str
    role_in_case: str
    actor_user_id: str


class InternalNcTeamMemberResponse(BaseModel):
    id: str
    nonconformity_id: str
    user_id: str
    role_in_case: str
    joined_at: datetime


class AddInternalNcCommentBody(BaseModel):
    comment_type: str = "general"
    content: str
    is_internal: bool = True
    created_by_user_id: str


class InternalNcCommentResponse(BaseModel):
    id: str
    nc_type: str
    nc_id: str
    comment_type: str
    content: str
    is_internal: bool
    created_by_user_id: str
    created_at: datetime

class UploadInternalNcAttachmentBody(BaseModel):
    file_name: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str] = None
    uploaded_by_user_id: str


class UploadInternalNcActionAttachmentBody(BaseModel):
    file_name: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str] = None
    uploaded_by_user_id: str


class InternalNcAttachmentResponse(BaseModel):
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


class InternalNcFullDetailsResponse(BaseModel):
    nonconformity: dict[str, Any]
    root_causes: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    effectiveness_checks: list[dict[str, Any]]
    comments: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    team_members: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]

class UploadInternalNcAttachmentBody(BaseModel):
    file_name: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str] = None
    uploaded_by_user_id: str


class UploadInternalNcActionAttachmentBody(BaseModel):
    file_name: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str] = None
    uploaded_by_user_id: str


class InternalNcAttachmentResponse(BaseModel):
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