from __future__ import annotations

from datetime import date

from app.application.dto.audit_5s.list_audit_5s_nc_board_request import (
    ListAudit5sNcBoardRequest,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


class _FilterProbe(PostgresAudit5sRepository):
    def __init__(self) -> None:
        pass


def test_nc_board_filter_omits_dates_when_open() -> None:
    clause, params = _FilterProbe()._nc_board_filter_clause(
        ListAudit5sNcBoardRequest(branch_code="01"),
    )
    assert "audit_date BETWEEN" not in clause
    assert params == ["01"]


def test_nc_board_filter_applies_dates_when_provided() -> None:
    clause, params = _FilterProbe()._nc_board_filter_clause(
        ListAudit5sNcBoardRequest(
            branch_code="01",
            date_start=date(2026, 7, 1),
            date_end=date(2026, 7, 14),
        ),
    )
    assert "audit_date BETWEEN" in clause
    assert params == ["01", "2026-07-01", "2026-07-14"]


def test_nc_board_filter_pending_and_responsible_user() -> None:
    clause, params = _FilterProbe()._nc_board_filter_clause(
        ListAudit5sNcBoardRequest(
            branch_code="02",
            pending_only=True,
            responsible_user_id="user-42",
        ),
    )
    assert "nc.status IN ('open', 'in_progress')" in clause
    assert "nc.responsible_user_id = %s" in clause
    assert "user-42" in params


def test_nc_board_excludes_candidates_for_my_pending_scope() -> None:
    included = _FilterProbe()._nc_board_includes_candidates(
        ListAudit5sNcBoardRequest(
            branch_code="01",
            pending_only=True,
            responsible_user_id="user-42",
        ),
    )
    assert included is False
