from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder
from app.application.use_cases.audit_5s.get_audit_5s_dashboard_use_case import (
    GetAudit5sDashboardUseCase,
)


def _repo_dashboard_payload(*, total: int = 1, page: int = 1, page_size: int = 20) -> dict:
    """Shape returned by PostgresAudit5sRepository.get_dashboard (canonical envelope)."""
    return {
        "summary": {
            "audit_count": total,
            "average_score_pct": 85.5,
            "nc_total": 0,
            "nc_open": 0,
            "nc_closed": 0,
            "nc_overdue": 0,
            "filtered_senso_order": None,
            "filtered_senso_name": None,
        },
        "charts": {
            "score_by_period": [],
            "score_by_area": [],
            "score_by_senso": [],
            "nc_by_status": [],
        },
        "items": [
            {
                "id": "aud-1",
                "audit_code": "A5S-001",
                "audit_date": "2026-09-22",
                "area_name": "Área A",
                "shift": "TURNO_1",
                "status": "closed",
                "overall_score_pct": 85.5,
                "nc_total": 0,
                "nc_open": 0,
            }
        ]
        if total
        else [],
        "pagination": PaginationEnvelopeBuilder.paged_count(
            page=page,
            page_size=page_size,
            total=total,
        ),
    }


def test_dashboard_accepts_canonical_paged_count_envelope() -> None:
    """Regression: repo emits total_pages/is_complete; DTO must not unpack them as fields."""
    repository = MagicMock()
    repository.get_dashboard.return_value = _repo_dashboard_payload(total=45, page=2, page_size=20)

    result = GetAudit5sDashboardUseCase(repository).execute(
        branch_code="02",
        date_start="2026-09-22",
        date_end="2026-09-22",
        granularity="month",
        page=2,
        page_size=20,
    )

    assert result.pagination.page == 2
    assert result.pagination.page_size == 20
    assert result.pagination.total == 45
    assert result.pagination.total_pages == 3
    payload = result.to_dict()["pagination"]
    assert payload["total_pages"] == 3
    assert payload["is_complete"] is False
    assert len(result.items) == 1


def test_dashboard_sibling_empty_period() -> None:
    repository = MagicMock()
    repository.get_dashboard.return_value = _repo_dashboard_payload(total=0)

    result = GetAudit5sDashboardUseCase(repository).execute(
        branch_code="01",
        date_start="2026-09-22",
        date_end="2026-09-22",
    )

    assert result.summary.audit_count == 0
    assert result.pagination.total == 0
    assert result.pagination.total_pages == 0
    assert result.to_dict()["pagination"]["is_complete"] is True
    assert result.items == []


def test_dashboard_rejects_invalid_branch() -> None:
    use_case = GetAudit5sDashboardUseCase(MagicMock())

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(
            branch_code="99",
            date_start="2026-09-22",
            date_end="2026-09-22",
        )


def test_dashboard_request_dates_forwarded() -> None:
    repository = MagicMock()
    repository.get_dashboard.return_value = _repo_dashboard_payload(total=0)

    GetAudit5sDashboardUseCase(repository).execute(
        branch_code="02",
        date_start="2026-09-01",
        date_end="2026-09-22",
        area_id="area-1",
        shift="TURNO_1",
    )

    request = repository.get_dashboard.call_args[0][0]
    assert request.branch_code == "02"
    assert request.date_start == date(2026, 9, 1)
    assert request.date_end == date(2026, 9, 22)
    assert request.area_id == "area-1"
    assert request.shift == "TURNO_1"
