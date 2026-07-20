"""Unit tests for audit_route_test_coverage helpers."""

from __future__ import annotations

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT / "scripts"))

from audit_route_test_coverage import build_coverage  # noqa: E402


def test_build_coverage_marks_covered_and_exempt() -> None:
    baseline = {
        "operation_count": 3,
        "operations": [
            {
                "method": "GET",
                "path": "/health",
                "operationId": "get_health",
                "xDelpi": {"entity": "health", "shape": "scalar"},
            },
            {
                "method": "GET",
                "path": "/supplies/otd",
                "operationId": "get_supplies_otd",
                "xDelpi": {"entity": "supplies_otd", "shape": "scalar"},
            },
            {
                "method": "POST",
                "path": "/canal-denuncia/denuncias",
                "operationId": "create_canal_denuncia",
                "xDelpi": {"entity": "canal_denuncia", "shape": "scalar"},
            },
        ],
    }
    coverage = build_coverage(
        baseline,
        test_blob='assert operation_id == "get_supplies_otd"\n',
        previous_coverage=Path("/nonexistent"),
    )
    by_oid = {op["operationId"]: op for op in coverage["operations"]}
    assert by_oid["get_health"]["status"] == "exempt"
    assert by_oid["get_supplies_otd"]["status"] == "covered"
    assert by_oid["create_canal_denuncia"]["status"] == "gap"
    assert coverage["coveredCount"] == 1
    assert coverage["gapCount"] == 1
    assert coverage["exemptCount"] == 1
