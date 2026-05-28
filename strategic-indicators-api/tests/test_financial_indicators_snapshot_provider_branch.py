from __future__ import annotations

from unittest.mock import MagicMock

from si_app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)


def test_get_financial_snapshot_passes_branch_to_service() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = MagicMock(branches=[])
    provider = FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=service,
    )

    provider.get_financial_indicators_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch="01",
    )

    service.get_snapshot.assert_called_once_with(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch="01",
    )


def test_get_financial_snapshot_series_passes_branch_to_service() -> None:
    service = MagicMock()
    service.get_snapshot_series.return_value = {}
    provider = FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=service,
    )
    period = MagicMock(competence="2026-05")

    provider.get_financial_indicators_snapshot_series(
        periods=[period],
        branch="02",
    )

    service.get_snapshot_series.assert_called_once_with(
        periods=[period],
        branch="02",
    )
