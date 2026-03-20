# app/domain/entities/external_nc/external_nonconformity.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class ExternalNonconformity:
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