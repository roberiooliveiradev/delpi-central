from unittest.mock import MagicMock

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.models.page import Page
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    DASHBOARD_SCOPE_AGGREGATES,
    DASHBOARD_SCOPE_ITEMS,
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


def test_dashboard_aggregates_scope_uses_summary_repository() -> None:
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        {
            "branch": "01",
            "sale_number": "OV001",
            "listing_kind": "LMP",
            "start_date": "20260501",
            "end_date": "20260510",
            "engineering_status": "Em andamento",
            "engineering_total_minutes": 120,
            "qtd_pi": 2,
        }
    ]

    use_case = ListLMPDashboardUseCase(repository)
    result = use_case.execute(
        ListLMPRequest(date_start="20260501", date_end="20260522", branch="01"),
        scope=DASHBOARD_SCOPE_AGGREGATES,
    )

    repository.get_lmp_dashboard_summary.assert_called_once()
    repository.list_lmps.assert_not_called()
    repository.list_lmps_page.assert_not_called()
    assert result["items"] == []
    assert result["summary"]["total_items"] == 1
    assert result["charts"]["levelData"]


def test_dashboard_items_scope_uses_paged_repository() -> None:
    repository = MagicMock()
    repository.list_lmps_page.return_value = Page(
        items=[_sample_lmp()],
        total=1,
        page=1,
        page_size=50,
    )

    use_case = ListLMPDashboardUseCase(repository)
    result = use_case.execute(
        ListLMPRequest(date_start="20260501", date_end="20260522"),
        scope=DASHBOARD_SCOPE_ITEMS,
    )

    repository.list_lmps_page.assert_called_once()
    repository.get_lmp_dashboard_summary.assert_not_called()
    assert len(result["items"]) == 1
    assert result["summary"] is None
    assert result["charts"] is None
