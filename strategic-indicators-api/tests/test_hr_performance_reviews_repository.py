from __future__ import annotations

from unittest.mock import MagicMock

from si_app.infrastructure.persistence.portal_rh.hr_repositories.hr_metrics_repository import (
    PERFORMANCE_REVIEWS_INDICATOR_CODES,
    HrMetricsRepository,
)


def test_performance_reviews_reads_monthly_actual_percent() -> None:
    repo = HrMetricsRepository(connection=MagicMock())
    repo._get_branch_indicator_average_or_latest_value = MagicMock(
        return_value={
            "value": 94.92,
            "measurement_date": "2026-05-01",
            "effective_date": "31-05-2026",
            "used_fallback": False,
        }
    )

    result = repo.get_performance_reviews_completion_snapshot(
        branch_code="01",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    repo._get_branch_indicator_average_or_latest_value.assert_called_once_with(
        branch_code="01",
        start_date="01-05-2026",
        end_date="31-05-2026",
        indicator_codes=list(PERFORMANCE_REVIEWS_INDICATOR_CODES),
    )
    assert result["indicator_code"] == "DES_AVL"
    assert result["value"] == 94.92
    assert result["branch_code"] == "01"


def test_performance_reviews_indicator_codes_include_portal_rh_catalog() -> None:
    assert PERFORMANCE_REVIEWS_INDICATOR_CODES[0] == "DES_AVL"
    assert "AVA_DES" in PERFORMANCE_REVIEWS_INDICATOR_CODES
