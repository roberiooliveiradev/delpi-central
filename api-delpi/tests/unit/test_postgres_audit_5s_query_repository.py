from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_query_repository import (
    PostgresAudit5SQueryRepository,
)


def _row(**overrides) -> dict:
    base = {
        "id": UUID("11111111-2222-3333-4444-555555555555"),
        "branch_code": "01",
        "audit_code": "01-000117",
        "audit_date": date(2026, 7, 23),
        "area_responsible": "PCP",
        "shift": "Administrativo",
        "status": "nc_in_progress",
        "overall_score_pct": Decimal("97.33"),
        "area_name": "PCP",
        "auditor_names": "Lucas Santos Garcia",
    }
    base.update(overrides)
    return base


def _repository(rows: list[dict]) -> PostgresAudit5SQueryRepository:
    repo = PostgresAudit5SQueryRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(return_value=rows)
    return repo


def test_postgres_audit_5s_summary_averages_scores_in_range() -> None:
    repository = _repository(
        [
            _row(overall_score_pct=Decimal("100.00")),
            _row(
                id=UUID("22222222-2222-3333-4444-555555555555"),
                overall_score_pct=Decimal("80.00"),
                audit_code="01-000116",
            ),
        ]
    )

    summary = repository.get_audit_summary(
        Audit5SSummaryRequest(
            start_date="2026-07-01",
            end_date="2026-07-31",
            branch="01",
        )
    )

    assert summary.average_score == 90.0
    assert len(summary.list_audits) == 2
    assert summary.list_audits[0].average_line_score == 100.0
    assert summary.list_audits[0].inspection_number == "01-000117"
    assert summary.list_audits[0].date == "2026-07-23"
    assert summary.list_audits[0].branch == "01"

    sql = repository.fetch_all.call_args.args[0]
    params = repository.fetch_all.call_args.args[1]
    assert "a.status != 'draft'" in sql
    assert "a.overall_score_pct IS NOT NULL" in sql
    assert "a.branch_code = %s" in sql
    assert params == ("01", "2026-07-01", "2026-07-31")


def test_postgres_audit_5s_summary_omits_branch_filter_when_consolidated() -> None:
    repository = _repository([_row()])

    summary = repository.get_audit_summary(
        Audit5SSummaryRequest(
            start_date="2026-07-01",
            end_date="2026-07-31",
        )
    )

    assert summary.average_score == 97.33
    sql = repository.fetch_all.call_args.args[0]
    params = repository.fetch_all.call_args.args[1]
    assert "a.branch_code = %s" not in sql
    assert params == ("2026-07-01", "2026-07-31")


def test_postgres_audit_5s_summary_empty_returns_zero_average() -> None:
    repository = _repository([])

    summary = repository.get_audit_summary(
        Audit5SSummaryRequest(
            start_date="2026-07-01",
            end_date="2026-07-31",
            branch="01",
        )
    )

    assert summary.average_score == 0.0
    assert summary.list_audits == []
