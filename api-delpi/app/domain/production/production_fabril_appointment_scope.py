"""Escopo canônico de apontamentos produtivos (eficiência fabril / OEE alinhado)."""

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)

EFICIENCIA_FABRIL_VIEW = "dbo.vw_Apontamentos_Eficiencia"
STATUS_REGISTRO_OK = "OK"
DEFAULT_PRODUCTION_BRANCHES = ("01", "02")
EXCLUDED_WORK_CENTERS = ("CT-00", "CT-70", "CT-16A", "CT-99")

EFFICIENCY_PERCENTUAL_COLUMN = "EFICIENCIA_PERCENTUAL"
