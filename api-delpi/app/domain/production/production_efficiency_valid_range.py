"""Faixa válida de eficiência (%) para indicadores de produção.

Usada por OEE (H6_ZEFICI / SH6010) e Eficiência Fabril (EFICIENCIA_PERCENTUAL / view).
Valores fora da faixa permanecem listáveis, mas não entram em médias/KPIs/gráficos.
"""

PRODUCTION_EFFICIENCY_VALID_MIN_PCT = 0
PRODUCTION_EFFICIENCY_VALID_MAX_PCT = 199
PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD = 50


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


def is_low_production_efficiency_pct(value: float | int | None) -> bool:
    if not is_valid_production_efficiency_pct(value):
        return False
    try:
        pct = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return pct < PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD


EFFICIENCY_BAND_OK = "ok"
EFFICIENCY_BAND_LOW = "low"
EFFICIENCY_BAND_VERIFY = "verify"
EFFICIENCY_BANDS = frozenset(
    {EFFICIENCY_BAND_OK, EFFICIENCY_BAND_LOW, EFFICIENCY_BAND_VERIFY}
)


def parse_efficiency_bands(raw: str | list[str] | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        parts = [part.strip().lower() for part in raw.split(",")]
    else:
        parts = [str(part).strip().lower() for part in raw]
    return [part for part in parts if part in EFFICIENCY_BANDS]


def build_efficiency_bands_where_clause(
    bands: list[str],
    *,
    status_column: str = "status",
    pct_column: str = "oee_pct",
) -> str:
    if not bands:
        return ""

    conditions: list[str] = []
    if EFFICIENCY_BAND_VERIFY in bands:
        conditions.append(f"{status_column} = 'outlier'")
    if EFFICIENCY_BAND_LOW in bands:
        conditions.append(
            f"({status_column} = 'valid' AND {pct_column} < {PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD})"
        )
    if EFFICIENCY_BAND_OK in bands:
        conditions.append(
            f"({status_column} = 'valid' AND {pct_column} >= {PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD})"
        )

    if not conditions:
        return ""

    return f"WHERE ({' OR '.join(conditions)})"


def resolve_production_list_status_filter_clause(
    status: str | None,
    efficiency_bands: str | list[str] | None,
    *,
    status_column: str = "status",
    pct_column: str = "oee_pct",
) -> str:
    bands = parse_efficiency_bands(efficiency_bands)
    if bands:
        return build_efficiency_bands_where_clause(
            bands,
            status_column=status_column,
            pct_column=pct_column,
        )

    normalized = (status or "").strip().lower()
    if normalized == "valid":
        return f"WHERE {status_column} = 'valid'"
    if normalized == "outlier":
        return f"WHERE {status_column} = 'outlier'"
    return ""
