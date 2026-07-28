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


def _summary_fact_row(**overrides) -> dict:
    base = {
        "branch": "01",
        "sale_number": "OV001",
        "sale_description": "Projeto",
        "listing_kind": "LMP",
        "start_date": "20260501",
        "end_date": "20260510",
        "homolog_revision": "001",
        "measurement_revision": "001",
        "homolog_date": "20260501",
        "cycle_index": 1,
        "engineering_status": "FINALIZADA",
        "engineering_total_minutes": 60,
        "qtd_pi": 0,
    }
    base.update(overrides)
    return base


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


def test_execute_summary_kpi_loads_pi_only_for_finished_ovs() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary_facts.return_value = [
        _summary_fact_row(
            sale_number="OVFIN",
            engineering_status="FINALIZADA",
            engineering_total_minutes=60,
        ),
        _summary_fact_row(
            sale_number="OVOPEN",
            engineering_status="EM_ANDAMENTO",
            end_date=None,
            engineering_total_minutes=99999,
        ),
    ]
    repository.get_lmp_pi_counts_by_ovs.return_value = {
        ("01", "OVFIN", "001"): 2,
    }

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")
    summary = use_case.execute_summary(request)

    repository.get_lmp_dashboard_summary_facts.assert_called_once()
    repository.get_lmp_pi_counts_by_ovs.assert_called_once()
    called_keys = repository.get_lmp_pi_counts_by_ovs.call_args.kwargs["ov_keys"]
    assert called_keys == [
        {"branch": "01", "sale_number": "OVFIN", "revision": "001"},
    ]
    repository.get_lmp_dashboard_summary.assert_not_called()
    assert summary["total_lmps"] == 2
    assert summary["percent_dentro_prazo"] == 100.0


def test_execute_summary_caches_response_without_second_repository_call() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary_facts.return_value = [
        _summary_fact_row(),
    ]
    repository.get_lmp_pi_counts_by_ovs.return_value = {("01", "OV001", "001"): 0}

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    first = use_case.execute_summary(request)
    second = use_case.execute_summary(request)

    assert first["total_lmps"] == 1
    assert second == first
    repository.get_lmp_dashboard_summary_facts.assert_called_once()
    repository.get_lmp_pi_counts_by_ovs.assert_called_once()


def test_execute_charts_uses_full_pi_batch() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        _summary_fact_row(qtd_pi=3),
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    charts = use_case.execute_charts(request)

    repository.get_lmp_dashboard_summary.assert_called_once()
    assert repository.get_lmp_dashboard_summary.call_args.args[0].include_qtd_pi is True
    repository.get_lmp_dashboard_summary_facts.assert_not_called()
    assert charts["levelData"]


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
        "app.application.use_cases.lmp.list_lmp_dashboard_use_case.get_or_set_cached_lmp_dashboard",
        side_effect=lambda key, factory: (
            cached_charts if key.endswith("|charts-response") else factory()
        ),
    ):
        result = use_case.execute_charts(request)

    assert result == cached_charts
    repository.get_lmp_dashboard_summary.assert_not_called()


def test_summary_kpi_and_full_use_distinct_cache_keys() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary_facts.return_value = [
        _summary_fact_row(qtd_pi=0),
    ]
    repository.get_lmp_pi_counts_by_ovs.return_value = {("01", "OV001", "001"): 2}
    repository.get_lmp_dashboard_summary.return_value = [
        _summary_fact_row(qtd_pi=2),
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    kpi = use_case.execute_summary(request, summary_mode="kpi")
    full = use_case.execute_summary(request, summary_mode="full")
    use_case.execute_items(request)

    assert kpi["percent_dentro_prazo"] == full["percent_dentro_prazo"]
    assert repository.get_lmp_dashboard_summary_facts.call_count == 1
    # full summary + items compartilham `|summary-rows|pi1`
    assert repository.get_lmp_dashboard_summary.call_count == 1
    assert repository.get_lmp_pi_counts_by_ovs.call_count == 1


def test_full_items_reuses_full_summary_rows_cache() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_lmp_dashboard_summary.return_value = [
        _summary_fact_row(qtd_pi=1),
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    use_case.execute_charts(request)
    use_case.execute_items(request)

    repository.get_lmp_dashboard_summary.assert_called_once()


def test_kpi_percent_matches_full_when_same_finished_pi() -> None:
    """Paridade: % prazo kpi == full com mesmas finalizadas + mesmos PI."""
    reset_query_cache_for_tests()
    finished = _summary_fact_row(
        sale_number="OVFIN",
        engineering_status="FINALIZADA",
        engineering_total_minutes=60,
        qtd_pi=0,
    )
    open_row = _summary_fact_row(
        sale_number="OVOPEN",
        engineering_status="EM_ANDAMENTO",
        end_date=None,
        engineering_total_minutes=99999,
        qtd_pi=0,
    )

    repository = MagicMock()
    repository.get_lmp_dashboard_summary_facts.return_value = [finished, open_row]
    repository.get_lmp_pi_counts_by_ovs.return_value = {
        ("01", "OVFIN", "001"): 5,
    }
    repository.get_lmp_dashboard_summary.return_value = [
        {**finished, "qtd_pi": 5},
        {**open_row, "qtd_pi": 99},  # PI em aberta não altera veredito
    ]

    use_case = ListLMPDashboardUseCase(repository)
    request = ListLMPRequest(date_start="20260501", date_end="20260522")

    kpi = use_case.execute_summary(request, summary_mode="kpi")
    full = use_case.execute_summary(request, summary_mode="full")

    assert kpi["percent_dentro_prazo"] == full["percent_dentro_prazo"]
    assert kpi["total_lmps"] == full["total_lmps"]
