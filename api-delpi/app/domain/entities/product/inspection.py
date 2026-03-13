# app/domain/entities/inspection.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InspectionHeader:
    product_code: str
    revision: str
    description: Optional[str]
    created_at: Optional[str]
    start_date: Optional[str]
    inspection_type: Optional[str]
    unit: Optional[str]


@dataclass
class MeasurableTests:
    test_code: str
    labor: Optional[str]
    sequence: Optional[int]
    unit: Optional[str]
    nominal_value: Optional[float]
    lower_spec_limit: Optional[float]
    upper_spec_limit: Optional[float]


@dataclass
class TextualTests:
    test_code: str
    labor: Optional[str]
    sequence: Optional[int]
    text: Optional[str]


@dataclass
class Inspection:
    product_code: str
    bom_level: int
    has_inspection: bool
    header: Optional[InspectionHeader]
    measurable_tests: List[MeasurableTests]
    textual_tests: List[TextualTests]