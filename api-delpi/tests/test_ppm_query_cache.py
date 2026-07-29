from unittest.mock import MagicMock, patch

from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.services.charts.chart_series_cache_keys import ppm_series_cache_key
from app.application.services.quality.ppm_query_cache import ppm_summary_cache_key
from app.application.use_cases.ppm.get_ppm_series_use_case import GetPpmSeriesUseCase
from app.application.use_cases.ppm.get_ppm_summary_use_case import GetPpmSummaryUseCase
from app.composition.query_cache_composer import build_query_cache, reset_query_cache_for_tests
from app.domain.entities.ppm.ppm_summary import PpmSummary
from app.domain.services.query_cache_stats_service import reset_query_cache_stats_for_tests


def setup_function() -> None:
    reset_query_cache_stats_for_tests()
    reset_query_cache_for_tests()


def test_ppm_summary_cache_key_varies_by_type() -> None:
    internal = PpmSummaryRequest(
        type="internal",
        date_start="2026-01-01",
        date_end="2026-01-31",
    )
    external = PpmSummaryRequest(
        type="external",
        date_start="2026-01-01",
        date_end="2026-01-31",
    )
    assert ppm_summary_cache_key(internal) != ppm_summary_cache_key(external)


def test_ppm_summary_use_case_reuses_cached_summary() -> None:
    repository = MagicMock()
    returned = MagicMock()
    returned.get_totals.return_value = {"qty_returned_un": 1.0, "nc_count": 1}
    produced = MagicMock()
    produced.get_totals.return_value = {
        "qty_produced_milheiro": 2.0,
        "qty_produced_un": 2000.0,
    }
    use_case = GetPpmSummaryUseCase(repository, produced, returned)
    request = PpmSummaryRequest(
        type="external",
        branch="01",
        date_start="2026-01-01",
        date_end="2026-01-31",
    )

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first.ppm == 500.0
    assert second.ppm == 500.0
    assert first.to_dict()["numerator"]["qty_returned_un"] == 1.0
    assert first.to_dict()["denominator"]["qty_produced_un"] == 2000.0
    returned.get_totals.assert_called_once()
    produced.get_totals.assert_called_once()


def test_ppm_series_use_case_caches_full_response() -> None:
    summary_uc = MagicMock(spec=GetPpmSummaryUseCase)
    summary_uc.execute.return_value = PpmSummary(
        type="external",
        branch=None,
        start_date="2026-05-01",
        end_date="2026-05-31",
        total_devolvido_un=1.0,
        total_produzido_milheiro=1.0,
        total_produzido_un=1000.0,
        ppm=1000.0,
    )

    use_case = GetPpmSeriesUseCase(summary_uc)
    request = PpmSeriesRequest(
        type="external",
        granularity="month",
        date_start="2026-05-01",
        date_end="2026-05-31",
    )

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first.points
    assert second.points[0].ppm == first.points[0].ppm
    assert summary_uc.execute.call_count == 1

    cache_key = ppm_series_cache_key(request)
    assert build_query_cache().get(cache_key) is not None
