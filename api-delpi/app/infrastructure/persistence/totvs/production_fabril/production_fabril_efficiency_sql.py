"""Expressões SQL compartilhadas para eficiência da view fabril."""

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)
from app.domain.production.production_fabril_appointment_scope import (
    EFFICIENCY_PERCENTUAL_COLUMN,
)


def fabril_efficiency_pct_expr(column: str = EFFICIENCY_PERCENTUAL_COLUMN) -> str:
    return f"TRY_CAST({column} AS DECIMAL(18, 4))"


def fabril_efficiency_status_expr(column: str = EFFICIENCY_PERCENTUAL_COLUMN) -> str:
    pct = fabril_efficiency_pct_expr(column)
    return f"""
CASE
    WHEN {pct} BETWEEN {PRODUCTION_EFFICIENCY_VALID_MIN_PCT} AND {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}
    THEN 'valid'
    ELSE 'outlier'
END
"""
