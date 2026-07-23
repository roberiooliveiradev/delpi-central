from unittest.mock import MagicMock, patch

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    DEFAULT_DASHBOARD_PAGE_SIZE,
    ListLMPDashboardUseCase,
)
from app.composition.query_cache_composer import reset_query_cache_for_tests
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
    assert result["items"][0]["start_date"] == "2026-05-01"
    assert result["items"][0]["end_date"] == "2026-05-10"
    assert result["items"][0]["data_limite"] == "2026-05-07"
    assert result["items"][0]["homolog_date"] == "2026-05-01"


def test_execute_summary_caches_response_without_second_repository_call() -> None:
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        {
            "branch": "01",
            "sale_number": "OV001",
            "sale_description": "Projeto",
            "listing_kind": "LMP",
            "start_date": "20260501",
            "end_date": "20260510",
            "engineering_status": "Finalizado",
            "engineering_total_minutes": 60,
            "qtd_pi": 0,
        }
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    cached_response = {
        "total_lmps": 1,
        "total_items": 1,
        "percent_dentro_prazo": 100.0,
        "avg_lead_time": 5.0,
    }
    summary_response_reads = {"count": 0}

    def _get_cache_side_effect(key: str):
        if key.endswith("|summary-response"):
            summary_response_reads["count"] += 1
            if summary_response_reads["count"] > 1:
                return cached_response
        return None

    with patch(
        "app.application.use_cases.lmp.list_lmp_dashboard_use_case.get_cached_lmp_dashboard",
        side_effect=_get_cache_side_effect,
    ), patch(
        "app.application.use_cases.lmp.list_lmp_dashboard_use_case.set_cached_lmp_dashboard",
    ) as set_cache_mock:
        first = use_case.execute_summary(request)
        second = use_case.execute_summary(request)

    assert first["total_lmps"] == 1
    assert second == cached_response
    repository.get_lmp_dashboard_summary.assert_called_once()
    set_cache_mock.assert_called()


def test_execute_charts_reuses_summary_rows_cache_without_second_repository_call() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        {
            "branch": "01",
            "sale_number": "OV001",
            "sale_description": "Projeto",
            "listing_kind": "LMP",
            "start_date": "20260501",
            "end_date": "20260510",
            "engineering_status": "Finalizado",
            "engineering_total_minutes": 60,
            "qtd_pi": 0,
        }
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    use_case.execute_summary(request)
    use_case.execute_charts(request)

    repository.get_lmp_dashboard_summary.assert_called_once()


def test_execute_charts_returns_cached_response_without_repository_call() -> None:
    repository = MagicMock()
    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    cached_charts = {
        "levelData": [{"name": "Nível 1", "value": 1}],
        "statusData": [{"name": "Pontual", "value": 1}],
        "leadByLevel": [{"nivel": "Nível 1", "valor": 3.0}],
    }

    with patch(
        "app.application.use_cases.lmp.list_lmp_dashboard_use_case.get_cached_lmp_dashboard",
        side_effect=lambda key: cached_charts if key.endswith("|charts-response") else None,
    ):
        result = use_case.execute_charts(request)

    assert result == cached_charts
    repository.get_lmp_dashboard_summary.assert_not_called()


def test_summary_rows_cache_hit_with_real_query_cache() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        {
            "branch": "01",
            "sale_number": "OV001",
            "sale_description": "Projeto",
            "listing_kind": "LMP",
            "start_date": "20260501",
            "end_date": "20260510",
            "engineering_status": "Finalizado",
            "engineering_total_minutes": 60,
            "qtd_pi": 0,
        }
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    use_case.execute_summary(request)
    use_case.execute_charts(request)
    use_case.execute_items(request)

    repository.get_lmp_dashboard_summary.assert_called_once()
