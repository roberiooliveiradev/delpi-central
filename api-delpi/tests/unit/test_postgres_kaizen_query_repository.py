from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_query_repository import (
    PostgresKaizenQueryRepository,
)


def _row(**overrides) -> dict:
    base = {
        "id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        "branch_code": "01",
        "title": "App resina CT-16",
        "accountable": "Ossamu",
        "sector": "Producao",
        "investment": Decimal("620.00"),
        "seconds_per_occurrence": Decimal("1015.96"),
        "occurrences_per_day": Decimal("0.21"),
        "hourly_cost": Decimal("127.16"),
        "daily_savings": Decimal("7.54"),
        "annual_savings": Decimal("2752.10"),
        "status": "implantado",
        "date_implemented": date(2026, 1, 16),
    }
    base.update(overrides)
    return base


def _repository(rows: list[dict]) -> PostgresKaizenQueryRepository:
    repo = PostgresKaizenQueryRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(return_value=rows)
    repo.fetch_one = MagicMock(return_value=None)
    return repo


def test_postgres_kaizen_summary_counts_implanted_in_range() -> None:
    repository = _repository([_row()])

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="2026-01-16",
            date_end="2026-01-18",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.list_kaizen[0].daily_savings == 7.54
    assert summary.total_savings == round(7.54 * 3, 2)


def test_postgres_kaizen_summary_excludes_non_implanted() -> None:
    repository = _repository([_row(status="recebido")])

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="2026-01-01",
            date_end="2026-01-31",
        )
    )

    assert summary.total_kaizens == 0
    assert summary.total_savings == 0.0


def test_postgres_kaizen_summary_counts_aprovado_without_savings() -> None:
    repository = _repository(
        [
            _row(
                status="aprovado",
                date_committee_approved=date(2026, 1, 20),
                date_implemented=None,
                daily_savings=Decimal("10.00"),
            )
        ]
    )

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="2026-01-01",
            date_end="2026-01-31",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.total_savings == 0.0


def test_postgres_kaizen_summary_aprovado_falls_back_to_implemented_date() -> None:
    repository = _repository(
        [
            _row(
                status="aprovado",
                date_committee_approved=None,
                date_implemented=date(2026, 1, 16),
            )
        ]
    )

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="2026-01-01",
            date_end="2026-01-31",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.total_savings == 0.0


def test_postgres_kaizen_get_by_id_accepts_uuid() -> None:
    row = _row()
    repository = PostgresKaizenQueryRepository(connection=MagicMock())
    repository.fetch_all = MagicMock(return_value=[row])
    repository.fetch_one = MagicMock(return_value=row)

    detail = repository.get_kaizen_by_id("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    assert detail is not None
    assert detail.title == "App resina CT-16"
    assert detail.daily_savings == 7.54
    assert detail.hours_saved_per_day == pytest.approx(0.0593, rel=1e-3)


def test_postgres_kaizen_get_by_id_accepts_legacy_sheet_id() -> None:
    row = _row()
    repository = PostgresKaizenQueryRepository(connection=MagicMock())
    repository.fetch_all = MagicMock(return_value=[row])
    repository.fetch_one = MagicMock(return_value=None)

    detail = repository.get_kaizen_by_id("01-16/01/2026-App resina CT-16")

    assert detail is not None
    assert detail.title == "App resina CT-16"


def test_postgres_kaizen_get_by_id_returns_none_when_missing() -> None:
    repository = PostgresKaizenQueryRepository(connection=MagicMock())
    repository.fetch_all = MagicMock(return_value=[])
    repository.fetch_one = MagicMock(return_value=None)

    assert repository.get_kaizen_by_id("inexistente") is None
