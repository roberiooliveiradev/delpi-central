from dataclasses import dataclass
from typing import Optional


@dataclass
class GetProductionOeeRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    efficiency_bands: Optional[str] = None
    work_center: Optional[str] = None
    production_order: Optional[str] = None
    operator_code: Optional[str] = None
    product_type: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_dir: str = "asc"
