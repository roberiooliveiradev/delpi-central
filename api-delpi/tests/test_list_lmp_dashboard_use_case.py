from unittest.mock import MagicMock

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    DEFAULT_DASHBOARD_PAGE_SIZE,
    ListLMPDashboardUseCase,
)
from app.domain.entities.lmp.lmp import LMP


def _sample_lmp(**overrides) -> LMP:
    base = {
        "branch": "01",
        "sale_number": "OV001",
        "sale_description": "Projeto teste",
        "listing_kind": "LMP",
        "start_date": "20260501",
        "end_date": "20260510",
        "engineering_status": "Em andamento",
        "engineering_total_minutes": 120,
        "qtd_pi": 2,
    }
    base.update(overrides)
    return LMP(**base)


def test_dashboard_paginates_items_and_builds_summary() -> None:
    repository = MagicMock()
    repository.list_lmps.return_value = [
        _sample_lmp(sale_number=f"OV{i:03d}") for i in range(3)
    ]

    use_case = ListLMPDashboardUseCase(repository)
    result = use_case.execute(
        ListLMPRequest(date_start="20260501", date_end="20260522"),
        status_filter="Todos",
    )

    repository.list_lmps.assert_called_once()
    repository.get_lmp_dashboard_summary.assert_not_called()
    repository.list_lmps_page.assert_not_called()
    assert result["page"] == 1
    assert result["page_size"] == DEFAULT_DASHBOARD_PAGE_SIZE
    assert len(result["items"]) == 3
    assert result["total"] == 3
    assert result["summary"]["total_items"] == 3
    assert result["charts"]["levelData"]
