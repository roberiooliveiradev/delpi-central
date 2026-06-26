# app/domain/entities/nonconformity/nonconformity.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Nonconformity:
    branch: str
    code: str
    revision: str
    type_code: str
    code_display: Optional[str] = None
    type_label: Optional[str] = None
    status_code: Optional[str] = None
    status_label: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    item_code: Optional[str] = None
    op_code: Optional[str] = None
    registered_date: Optional[str] = None
    occurrence_date: Optional[str] = None
    priority_code: Optional[str] = None
    priority_label: Optional[str] = None
    origin_department: Optional[str] = None
    destination_department: Optional[str] = None
    customer_code: Optional[str] = None
    customer_store: Optional[str] = None
    customer_name: Optional[str] = None
    supplier_code: Optional[str] = None
    supplier_store: Optional[str] = None
    produced_quantity: Optional[float] = None
    returned_quantity: Optional[float] = None