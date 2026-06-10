"""Casos por forma de dados — Playbook 13 §17 (shape-first, não só rota)."""

from __future__ import annotations

from typing import Any

HUMANIZED_DATA_SHAPE_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "field_value_profile",
        "shape": "field_value_profile",
        "profile_key": "factory_status",
        "path": "/products/90262404/factory-status",
        "data": {
            "factory_status": "PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL",
            "structure": {"summary": {"total_raw_materials": 3}},
            "production": {"summary": {"pa_production_started": True, "total_pa_orders": 12}},
            "shipping": {"summary": {"total_shipped_quantity": 0}},
            "raw_material_stock": {"items": [], "summary": {"total_without_stock_for_one_pa": 0}},
        },
        "expect": {
            "summary_answer": True,
            "recommendations_with_query": True,
        },
    },
    {
        "id": "generic_list",
        "shape": "generic_list",
        "profile_key": "stock",
        "path": "/products/90269001/stock",
        "data": {
            "items": [
                {"branch": "01", "warehouse": "A1", "available": 80, "committed": 10},
                {"branch": "02", "warehouse": "B2", "available": 70, "committed": 5},
            ],
            "summary": {"total_available": 150, "position_count": 2},
        },
        "expect": {
            "summary_answer": True,
            "recommendations_with_query": True,
        },
    },
    {
        "id": "categorical_ranking",
        "shape": "categorical_ranking",
        "profile_key": "generic",
        "path": "/commercial/closing-rate",
        "rows": [
            {"client": "A", "value": 40},
            {"client": "B", "value": 35},
            {"client": "C", "value": 25},
        ],
        "expect": {
            "summary_answer": True,
            "derived_metrics": True,
        },
    },
    {
        "id": "time_series",
        "shape": "time_series",
        "profile_key": "generic",
        "path": "/quality/nonconformities/series",
        "rows": [
            {"period": "jan/2026", "value": 4},
            {"period": "fev/2026", "value": 6},
            {"period": "mar/2026", "value": 5},
        ],
        "expect": {
            "summary_answer": True,
            "derived_metrics": True,
        },
    },
    {
        "id": "hierarchy",
        "shape": "hierarchy",
        "profile_key": "generic",
        "path": "/products/90269001/structure",
        "rows": [
            {"code": "PA-01", "children": [{"code": "MP-01", "quantity": 2}]},
        ],
        "expect": {
            "summary_answer": True,
        },
    },
    {
        "id": "kpi_set",
        "shape": "kpi_set",
        "profile_key": "generic",
        "path": "/commercial/closing-rate",
        "rows": [{"total": 125000, "target": 140000}],
        "expect": {
            "summary_answer": True,
            "derived_metrics": True,
        },
    },
    {
        "id": "empty_list",
        "shape": "empty_list",
        "profile_key": "generic",
        "path": "/supplies/cpv",
        "rows": [],
        "expect": {
            "summary_answer": True,
        },
    },
    {
        "id": "large_list",
        "shape": "large_list",
        "profile_key": "generic",
        "path": "/supplies/cpv",
        "rows": [{"name": f"Item {index}", "value": index} for index in range(1, 27)],
        "expect": {
            "summary_answer": True,
            "limitations": True,
        },
    },
    {
        "id": "truncated",
        "shape": "truncated",
        "profile_key": "stock",
        "path": "/products/90269001/stock",
        "data": {
            "items": [{"branch": "01", "warehouse": "A1", "available": 10, "committed": 0}],
            "summary": {"total_available": 10, "position_count": 1},
            "total": 12,
            "pagination": {"page": 1, "page_size": 1, "total": 12},
        },
        "expect": {
            "summary_answer": True,
            "limitations": True,
        },
    },
    {
        "id": "logical_error",
        "shape": "logical_error",
        "profile_key": "",
        "path": "/products/90269001/stock",
        "error_only": True,
        "expect": {
            "no_data_answer": True,
        },
    },
)

HUMANIZED_SHAPE_IDS: frozenset[str] = frozenset(
    str(case["shape"]) for case in HUMANIZED_DATA_SHAPE_CASES
)
