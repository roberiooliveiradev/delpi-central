from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class EficienciaFabrilQuerySettings:
    view_name: str = "dbo.vw_Apontamentos_Eficiencia"
    branches: List[str] = field(default_factory=lambda: ["01", "02"])
    default_page_size: int = 50
    max_page_size: int = 500
    max_date_range_days: int = 366
    top_operators_limit: int = 15
    top_work_centers_limit: int = 15
    status_registro_ok: str = "OK"
