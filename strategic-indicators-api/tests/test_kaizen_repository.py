from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from si_app.infrastructure.persistence.google_sheets.kaizen.kaizen_repository import (
    KaizenRepository,
)
from si_app.infrastructure.persistence.google_sheets.utils import Utils


def _build_repository(rows: list[dict]) -> KaizenRepository:
    client = MagicMock()
    client.read_csv_rows.return_value = rows
    return KaizenRepository(
        client=client,
        sheet_id="sheet",
        gid="gid",
        utils=Utils(),
    )


def test_kaizen_summary_counts_only_implemented_in_period() -> None:
    repository = _build_repository(
        [
            {
                "filial": "01",
                "descricao": "Jan",
                "status": "implantado",
                "data": "16/01/2026",
                "ganho_diario": "1",
                "deleted": "FALSE",
            },
            {
                "filial": "01",
                "descricao": "Abril",
                "status": "implantado",
                "data": "24/04/2026",
                "ganho_diario": "1",
                "deleted": "FALSE",
            },
            {
                "filial": "01",
                "descricao": "Aprovado sem implantar",
                "status": "aprovado",
                "data": "24/04/2026",
                "ganho_diario": "1",
                "deleted": "FALSE",
            },
        ]
    )

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            title=None,
            status=None,
            date_start="01-04-2026",
            date_end="30-04-2026",
            branch="01",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.list_kaizen[0].title == "Abril"
    assert summary.total_savings == 7.0


def test_kaizen_financial_gain_includes_implanted_before_period() -> None:
    repository = _build_repository(
        [
            {
                "filial": "01",
                "descricao": "Janeiro",
                "status": "implantado",
                "data": "16/01/2026",
                "ganho_diario": "10",
                "deleted": "FALSE",
            },
            {
                "filial": "01",
                "descricao": "Abril",
                "status": "implantado",
                "data": "24/04/2026",
                "ganho_diario": "5",
                "deleted": "FALSE",
            },
        ]
    )

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            title=None,
            status=None,
            date_start="01-04-2026",
            date_end="30-04-2026",
            branch="01",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.list_kaizen[0].title == "Abril"
    assert summary.total_savings == 10 * 30 + 5 * 7
