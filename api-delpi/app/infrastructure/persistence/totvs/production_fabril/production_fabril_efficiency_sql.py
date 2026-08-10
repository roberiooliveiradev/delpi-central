"""Expressões SQL canônicas de eficiência fabril / OEE.

Única fonte para previsto e % — alinhada a ``production_tempo_previsto.py``:

    tempo_previsto = setup + HY_TEMPAD × qtd_apontada
    eficiencia_%   = tempo_previsto / tempo_real × 100

Não usar ``EF.EFICIENCIA_PERCENTUAL`` cru da view nos KPIs (legado TEMPOM×qtd/C2).
"""

from __future__ import annotations

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)
from app.domain.production.production_fabril_appointment_scope import (
    EFFICIENCY_PERCENTUAL_COLUMN,
)

# Meta/hora = ritmo unitário do snapshot da OP (SHY), sem setup.
# HY_TEMPAD = h/unid congelado na OP (estável).
# HY_TEMPOM = HY_TEMPAD * HY_QUANT e muda com apontamento parcial — NÃO usar
# QTD_OP/HY_TEMPOM (meta oscila). Fallback: HY_QUANT/HY_TEMPOM; por fim SG2.
FABRIL_META_POR_HORA_SQL = """
CASE
    WHEN SHY.HY_TEMPAD IS NOT NULL AND SHY.HY_TEMPAD > 0
    THEN ROUND(1.0 / SHY.HY_TEMPAD, 6)
    WHEN NULLIF(SHY.HY_TEMPOM, 0) IS NOT NULL
     AND NULLIF(SHY.HY_QUANT, 0) IS NOT NULL
    THEN ROUND(SHY.HY_QUANT / SHY.HY_TEMPOM, 6)
    WHEN SG2.G2_TEMPAD IS NOT NULL AND SG2.G2_TEMPAD > 0
    THEN ROUND(1.0 / SG2.G2_TEMPAD, 6)
    ELSE NULL
END
"""

FABRIL_SETUP_HORAS_SQL = """
COALESCE(SHY.HY_SETUP, SG2.G2_SETUP, 0)
"""

FABRIL_UNIT_HOURS_SQL = """
CASE
    WHEN SHY.HY_TEMPAD IS NOT NULL AND SHY.HY_TEMPAD > 0
    THEN SHY.HY_TEMPAD
    WHEN NULLIF(SHY.HY_TEMPOM, 0) IS NOT NULL
     AND NULLIF(SHY.HY_QUANT, 0) IS NOT NULL
    THEN SHY.HY_TEMPOM / SHY.HY_QUANT
    WHEN SG2.G2_TEMPAD IS NOT NULL AND SG2.G2_TEMPAD > 0
    THEN SG2.G2_TEMPAD
    ELSE NULL
END
"""

FABRIL_TEMPO_PREVISTO_SQL = f"""
CASE
    WHEN ({FABRIL_UNIT_HOURS_SQL}) IS NOT NULL
     AND TRY_CAST(EF.QTD_APONTADA AS FLOAT) IS NOT NULL
     AND TRY_CAST(EF.QTD_APONTADA AS FLOAT) > 0
    THEN ROUND(
        ({FABRIL_SETUP_HORAS_SQL})
        + ({FABRIL_UNIT_HOURS_SQL}) * TRY_CAST(EF.QTD_APONTADA AS FLOAT),
        6
    )
    ELSE TRY_CAST(EF.TEMPO_PREVISTO_HORAS AS FLOAT)
END
"""

FABRIL_EFICIENCIA_PERCENTUAL_SQL = f"""
CASE
    WHEN TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT) > 0
     AND ({FABRIL_TEMPO_PREVISTO_SQL}) IS NOT NULL
    THEN ROUND(
        ({FABRIL_TEMPO_PREVISTO_SQL}) * 100.0 / TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT),
        2
    )
    ELSE NULL
END
"""

FABRIL_TEMPO_GANHO_PERDIDO_SQL = f"""
CASE
    WHEN ({FABRIL_TEMPO_PREVISTO_SQL}) IS NOT NULL
     AND TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT) IS NOT NULL
    THEN ROUND(
        ({FABRIL_TEMPO_PREVISTO_SQL}) - TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT),
        6
    )
    ELSE TRY_CAST(EF.TEMPO_GANHO_PERDIDO_HORAS AS FLOAT)
END
"""

# Alias estável para AVG/SUM/COUNT nos KPIs (subquery ``calc``).
FABRIL_KPI_EFFICIENCY_ALIAS = "efficiency_pct"


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


def fabril_recalculated_efficiency_status_expr() -> str:
    """Status valid/outlier sobre o % canônico (TEMPAD), não o da view."""
    return fabril_efficiency_status_expr(f"({FABRIL_EFICIENCIA_PERCENTUAL_SQL})")


def fabril_kpi_efficiency_in_valid_range_sql(
    *,
    alias: str = FABRIL_KPI_EFFICIENCY_ALIAS,
) -> str:
    """Filtro de KPI: só amostras na faixa 0–199 do % recalculado."""
    return (
        f"{alias} IS NOT NULL "
        f"AND {alias} >= {PRODUCTION_EFFICIENCY_VALID_MIN_PCT} "
        f"AND {alias} <= {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}"
    )
