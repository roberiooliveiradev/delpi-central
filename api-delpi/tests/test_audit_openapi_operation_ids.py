"""Inventário de operationId — estáveis vs auto-FastAPI."""

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT / "scripts"))

from audit_openapi_operation_ids import (  # noqa: E402
    build_inventory,
    extract_function_name,
    is_auto_operation_id,
    recommend_canonical,
)


def test_is_auto_operation_id() -> None:
    assert is_auto_operation_id("list_areas_quality_audit_5s_areas_get")
    assert not is_auto_operation_id("get_dashboard_department_idd")
    assert not is_auto_operation_id("get_sales_conversion_rate")


def test_extract_and_recommend_audit_5s() -> None:
    oid = "list_areas_quality_audit_5s_areas_get"
    path = "/quality/audit-5s/areas"
    fn = extract_function_name(oid, path, "GET")
    assert fn == "list_areas"
    assert recommend_canonical(fn, path, "Qualidade") == "list_audit_5s_areas"


def test_build_inventory_counts() -> None:
    import json

    baseline = json.loads(
        (API_ROOT / "app" / "content" / "openapi_baseline.json").read_text(encoding="utf-8")
    )
    inventory = build_inventory(baseline)
    assert inventory["operationCount"] == baseline["operation_count"]
    assert inventory["autoCount"] + inventory["stableCount"] == inventory["operationCount"]
    # Catálogo canônico: todos os operationId estáveis (sem auto-id FastAPI).
    assert inventory["autoCount"] == 0
    assert inventory["stableCount"] == inventory["operationCount"]
    assert not inventory["recommendationCollisions"]
