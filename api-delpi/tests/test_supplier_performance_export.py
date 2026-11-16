from unittest.mock import Mock
import pytest

from app.application.use_cases.supplies.get_supplier_performance_export_use_case import (
    GetSupplierPerformanceExportUseCase,
)


def inspection(code, store, ident, approved=1, rejected=0, **extra):
    return dict(branch="01", supplier_code=code, supplier_store=store,
                supplier_name="Fornecedor teste", inspection_id=str(ident),
                approved=approved, rejected=rejected, conditional=0, urgent=0, **extra)


def delivery(code, store, days):
    return dict(branch="01", supplier_code=code, supplier_store=store,
                supplier_name="Fornecedor teste", document="000012",
                order_number="001234", order_item="01", days_diff=days)


def test_export_uses_exact_detail_grain_and_recomputes_idf_without_stale_cache():
    repo = Mock()
    inspections = [inspection("000001", "01", i, approved=int(i < 8),
                              rejected=int(i >= 8)) for i in range(10)]
    deliveries = [delivery("000001", "01", 0 if i < 6 else -3) for i in range(10)]
    repo.read_evidence.return_value = (inspections, deliveries)
    result = GetSupplierPerformanceExportUseCase(repo).execute(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16",
        supplier_code="000001", supplier_store="01",
    )
    assert result["items"][0]["idf"] == 74
    assert result["summary"]["inspection_count"] == 10
    assert result["summary"]["receipt_count"] == 10
    assert len(result["inspections"]) == 10
    assert len(result["deliveries"]) == 10
    assert result["deliveries"][0]["document"] == "000012"
    assert result["inspections"][0]["evidence_state"] == "Aprovada"
    assert result["deliveries"][6]["evidence_state"] == "Atrasada"
    assert result["supplier_selected"] == {"code": "000001", "store": "01"}


def test_zero_is_valid_and_missing_data_is_not_zero():
    repo = Mock()
    repo.read_evidence.return_value = (
        [inspection("000001", "01", 1, approved=0, rejected=1),
         inspection("000002", "02", 2)],
        [delivery("000001", "01", -1)]
    )
    result = GetSupplierPerformanceExportUseCase(repo).execute(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16"
    )
    by_key = {item["supplier_code"]: item for item in result["items"]}
    assert by_key["000001"]["idf"] == 0.0
    assert by_key["000002"]["status"] == "missing_delivery"
    assert by_key["000002"]["idf"] is None


def test_undetermined_status_blocks_score_and_retains_detail():
    repo = Mock()
    repo.read_evidence.return_value = (
        [inspection("000001", "01", 1, approved=1, rejected=1)],
        [delivery("000001", "01", None)],
    )
    result = GetSupplierPerformanceExportUseCase(repo).execute(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16"
    )
    assert result["items"][0]["status"] == "inconsistent"
    assert result["items"][0]["idf"] is None
    assert result["inspections"][0]["evidence_state"] == "A revisar"
    assert result["deliveries"][0]["evidence_state"] == "Sem data válida"


@pytest.mark.parametrize("filters", [
    dict(supplier_code="000001"),
    dict(supplier_store="01"),
    dict(supplier_code="000001;DROP", supplier_store="01"),
])
def test_supplier_pair_validation_before_query(filters):
    repo = Mock()
    with pytest.raises(ValueError):
        GetSupplierPerformanceExportUseCase(repo).execute(
            branches=["01"], date_from="2026-11-01", date_to="2026-11-16",
            **filters,
        )
    repo.read_evidence.assert_not_called()
