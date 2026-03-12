# app/domain/entities/guide_operation.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class GuideOperation:

    branch: str
    route_code: str
    product_code: str

    operation_code: str
    operation_description: Optional[str]

    resource_code: Optional[str]
    work_center: Optional[str]

    setup_hours: Optional[float]

    standard_time_hour_mil: Optional[float]
    standard_time_hours_piece: Optional[float]
    standard_time_minutes_piece: Optional[float]

    operation_type: Optional[str]

    mandatory_operation: Optional[str]
    mandatory_sequence: Optional[str]
    mandatory_report: Optional[str]

    component_code: Optional[str]
    component_description: Optional[str]

    component_sequence: Optional[int]

    bom_level: int