import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.integrations.engineering_transforma_mais import (
    EngineeringProcessFilters,
    EngineeringTransformaMaisService,
)
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_legacy_contract(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    result = EngineeringTransformaMaisService().list_processes(EngineeringProcessFilters())

    assert result["total"] == 1
    item = result["items"][0]
    assert item["id"] == "p1"
    assert item["name_process"] == "Processo teste"
    assert item["daily_savings"] is not None
    assert item["daily_savings"] > 0


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_summary_legacy_contract_fields(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    data = EngineeringTransformaMaisService().get_summary(
        filial_id=None,
        start_date="2025-02-01",
        end_date="2025-02-28",
    )

    assert "implemented_solutions_count" in data
    assert "total_gross_savings_in_period" in data
    assert "monthly_breakdown" in data
    assert isinstance(data["monthly_breakdown"], list)
    if data["monthly_breakdown"]:
        month = data["monthly_breakdown"][0]
        assert "gross_savings_month" in month
        assert "net_savings_month" in month


@patch("tm_app.application.integrations.engineering_transforma_mais.DashboardDataRepository")
def test_list_processes_filter_by_filial(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    empty = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(filial_id="99")
    )
    assert empty["total"] == 0

    hit = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(filial_id="01")
    )
    assert hit["total"] == 1
