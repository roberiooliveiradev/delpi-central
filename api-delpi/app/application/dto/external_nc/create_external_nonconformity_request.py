# app/application/dto/external_nc/create_external_nonconformity_request.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class CreateExternalNonconformityRequest:
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