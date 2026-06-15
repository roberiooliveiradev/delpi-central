"""Faixa válida de eficiência (%) para indicadores de produção.

Usada por OEE (H6_ZEFICI / SH6010) e Eficiência Fabril (EFICIENCIA_PERCENTUAL / view).
Valores fora da faixa permanecem listáveis, mas não entram em médias/KPIs/gráficos.
"""

PRODUCTION_EFFICIENCY_VALID_MIN_PCT = 0
PRODUCTION_EFFICIENCY_VALID_MAX_PCT = 199


def is_valid_production_efficiency_pct(value: float | int | None) -> bool:
    if value is None:
        return False
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return False
    return (
        PRODUCTION_EFFICIENCY_VALID_MIN_PCT
        <= pct
        <= PRODUCTION_EFFICIENCY_VALID_MAX_PCT
    )
