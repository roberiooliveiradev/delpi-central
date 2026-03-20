# app/domain/entities/internal_nc/internal_nonconformity.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class InternalNonconformity:
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