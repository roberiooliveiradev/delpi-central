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
    
    def to_dict(self):

        return {
            "branch": self.branch,
            "route_code": self.route_code,
            "product_code": self.product_code,
            "operation_code": self.operation_code,
            "operation_description": self.operation_description,

            "resource_code": self.resource_code,
            "work_center": self.work_center,

            "setup_hours": self.setup_hours,
            "standard_time_hour_mil": self.standard_time_hour_mil,
            "standard_time_hours_piece": self.standard_time_hours_piece,
            "standard_time_minutes_piece": self.standard_time_minutes_piece,

            "operation_type": self.operation_type,
            "mandatory_operation": self.mandatory_operation,
            "mandatory_sequence": self.mandatory_sequence,
            "mandatory_report": self.mandatory_report,

            "component_code": self.component_code,
            "component_description": self.component_description,
            "component_sequence": self.component_sequence,

            "bom_level": self.bom_level
        }