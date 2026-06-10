"""Casos de regressão — apresentação rica e preferência de formato (Fase 0+)."""

from __future__ import annotations

from typing import Any

PRESENTATION_FORMAT_ALIASES: dict[str, str] = {
    "auto": "auto",
    "text": "text",
    "table": "table",
    "tree": "tree",
    "chart": "chart",
    "topics": "text",
    "canvas": "canvas",
}

PRESENTATION_DOMAIN_SAMPLES: tuple[dict[str, str], ...] = (
    {"domain": "product", "path": "/products/90269001/structure", "entity": "product_structure"},
    {"domain": "product", "path": "/products/90269001/stock", "entity": "product_stock"},
    {"domain": "supplies", "path": "/supplies/cpv", "entity": "supplies_cpv"},
    {"domain": "hr", "path": "/hr/snapshot", "entity": "hr_snapshot"},
    {"domain": "quality", "path": "/quality/nonconformities/series", "entity": "nonconformity_series"},
    {"domain": "commercial", "path": "/commercial/closing-rate", "entity": "sales_conversion_rate"},
    {"domain": "sql", "path": "/data/sql", "entity": "sql_result"},
    {"domain": "system", "path": "/system/tables/search", "entity": "protheus_table"},
)

PRESENTATION_SESSION_FORMAT_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "structure_prefers_table",
        "domain": "product",
        "path": "/products/90269001/structure",
        "session_format": "table",
        "expected_selected": "table",
        "expected_primary_type": "table",
    },
    {
        "id": "structure_prefers_tree",
        "domain": "product",
        "path": "/products/90269001/structure",
        "session_format": "tree",
        "expected_selected": "tree",
        "expected_primary_type": "tree",
    },
    {
        "id": "stock_prefers_chart",
        "domain": "product",
        "path": "/products/90269001/stock",
        "session_format": "chart",
        "expected_selected": "chart",
        "expected_primary_type": "chart",
    },
    {
        "id": "hr_snapshot_prefers_text",
        "domain": "hr",
        "path": "/hr/snapshot",
        "session_format": "text",
        "expected_selected": "text",
        "expected_primary_type": None,
    },
    {
        "id": "supplies_cpv_prefers_table",
        "domain": "supplies",
        "path": "/supplies/cpv",
        "session_format": "table",
        "expected_selected": "table",
        "expected_primary_type": "table",
    },
)

PRESENTATION_COVERAGE_EXPECTATIONS: dict[str, int] = {
    "min_operation_count": 130,
    "min_tier_a": 20,
    "min_tier_b": 25,
    "min_entity_routed": 55,
}

SCHEMA_DRIVEN_SAMPLE_PAYLOADS: tuple[dict[str, object], ...] = (
    {
        "id": "commercial_kpi_scalar",
        "path": "/commercial/closing-rate",
        "entity": "sales_conversion_rate",
        "data": {"value": 82.5, "target": 90.0, "previous": 80.0, "unit": "%"},
        "expected_primary_type": "kpi",
    },
    {
        "id": "quality_time_series",
        "path": "/quality/nonconformities/series",
        "entity": "nonconformity_series",
        "data": {
            "series": [
                {"period": "jan/2026", "value": 4},
                {"period": "fev/2026", "value": 6},
            ]
        },
        "expected_table_rows": 2,
        "expected_chart": True,
    },
    {
        "id": "hr_snapshot_scalar",
        "path": "/hr/snapshot",
        "entity": "hr_snapshot",
        "data": {
            "active_employees": 420,
            "turnover_pct": 3.2,
            "unit": "%",
        },
        "expected_primary_type": "kpi",
    },
    {
        "id": "financial_rol_series",
        "path": "/financial/rol",
        "entity": "financial_rol",
        "data": {
            "series": [
                {"period": "jan/2026", "value": 12.1},
                {"period": "fev/2026", "value": 12.8},
            ]
        },
        "expected_table_rows": 2,
        "expected_chart": True,
    },
    {
        "id": "quality_audit_summary_path_only",
        "path": "/quality/audit-5s/summary",
        "entity": None,
        "data": {
            "completed_audits": 18,
            "open_nonconformities": 4,
            "average_score": 87.5,
        },
        "expected_primary_type": "kpi",
    },
    {
        "id": "generic_hierarchy_tree",
        "path": "/engineering/transforma-mais/processes",
        "entity": "transforma_mais_process",
        "data": {
            "code": "TM-01",
            "description": "Processo piloto",
            "children": [
                {"code": "STEP-1", "description": "Mapeamento"},
                {"code": "STEP-2", "description": "Execução"},
            ],
        },
        "expected_tree": True,
    },
)
