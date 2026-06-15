from dataclasses import dataclass, field
from typing import List

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)


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
    # Alinhado a OEE (H6_ZEFICI): só entra em KPIs/gráficos dentro da faixa 0–199%.
    min_efficiency_indicator_pct: int = PRODUCTION_EFFICIENCY_VALID_MIN_PCT
    max_efficiency_indicator_pct: int = PRODUCTION_EFFICIENCY_VALID_MAX_PCT
