"""Constantes — KPI/chart presenter."""

from __future__ import annotations

# F2 — path fragment no-chart authority retired; use noChartEntities / is_no_chart_entity.
NO_CHART_PATHS: tuple[str, ...] = ()

CHART_WORTHY_NUMERIC_KEYS = {
        "quantity",
        "value",
        "total",
        "amount",
        "price",
        "cost",
        "revenue",
        "count",
        "percentage",
        "rate",
        "margin",
        "qtd",
        "qty",
        "consumption",
        "consumo",
        "valor",
        "preco",
        "custo",
        "receita",
        "faturamento",
        "saldo",
        "volume",
        "peso",
        "weight",
    }

# Canonical time-series list keys (aligned with schema-driven tabular list keys).
SERIES_LIST_KEYS = (
    "periods",
    "series",
    "history",
    "points",
)
