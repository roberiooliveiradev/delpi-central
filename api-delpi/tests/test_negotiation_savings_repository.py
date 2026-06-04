from unittest.mock import MagicMock

from app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)
from app.infrastructure.persistence.google_sheets.supplies.negotiation_savings_repository import (
    NegotiationSavingsRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils


def _repository(rows: list[dict]) -> NegotiationSavingsRepository:
    client = MagicMock()
    client.read_csv_rows.return_value = rows
    return NegotiationSavingsRepository(
        client=client,
        sheet_id="sheet-id",
        gid="gid",
        utils=Utils(),
    )


def test_negotiation_savings_summary_sums_by_branch_in_period() -> None:
    repository = _repository(
        [
            {
                "filial": "01",
                "data": "01/05/2026",
                "economia_reais": "R$ 15.000,00",
                "deleted": "FALSE",
            },
            {
                "filial": "02",
                "data": "01/05/2026",
                "economia_reais": "R$ 22.000,00",
                "deleted": "FALSE",
            },
            {
                "filial": "01",
                "data": "01/04/2026",
                "economia_reais": "R$ 1.000,00",
                "deleted": "FALSE",
            },
        ]
    )

    summary = repository.get_summary(
        NegotiationSavingsSummaryRequest(
            start_date="01-05-2026",
            end_date="31-05-2026",
        )
    )

    assert summary.total_savings == 37000.0
    assert len(summary.branches) == 2
    assert summary.branches[0].total_savings == 15000.0
    assert summary.branches[1].total_savings == 22000.0


def test_negotiation_savings_summary_filters_branch() -> None:
    repository = _repository(
        [
            {
                "filial": "1",
                "data": "01/05/2026",
                "economia_reais": "15000",
                "deleted": "FALSE",
            },
            {
                "filial": "02",
                "data": "01/05/2026",
                "economia_reais": "22000",
                "deleted": "FALSE",
            },
        ]
    )

    summary = repository.get_summary(
        NegotiationSavingsSummaryRequest(
            start_date="2026-05-01",
            end_date="2026-05-31",
            branch="01",
        )
    )

    assert summary.total_savings == 15000.0
    assert len(summary.branches) == 1
    assert summary.branches[0].branch == "01"


def test_negotiation_savings_summary_without_rows_returns_null_total() -> None:
    repository = _repository([])

    summary = repository.get_summary(
        NegotiationSavingsSummaryRequest(
            start_date="2026-06-01",
            end_date="2026-06-30",
        )
    )

    assert summary.total_savings is None
    assert summary.branches == []
