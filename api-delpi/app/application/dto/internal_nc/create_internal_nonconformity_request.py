from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class CreateInternalNonconformityRequest:
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