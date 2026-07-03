from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (
    PostgresKaizenRepository,
)


def _implanted_row(**overrides) -> dict:
    base = {
        "id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        "submodule_id": "sub",
        "branch_code": "01",
        "title": "Kaizen legado",
        "accountable": "Maria",
        "sector": "Producao",
        "investment": Decimal("100"),
        "savings_type": "tempo",
        "seconds_per_occurrence": Decimal("60"),
        "occurrences_per_day": Decimal("10"),
        "hourly_cost": Decimal("50"),
        "quantity_saved_per_day": None,
        "unit_material_cost": None,
        "fixed_daily_savings": None,
        "daily_savings": Decimal("8.33"),
        "annual_savings": Decimal("3040.45"),
        "realized_daily_savings": None,
        "realized_annual_savings": None,
        "status": "implantado",
        "date_implemented": date(2026, 6, 15),
        "date_discontinued": None,
        "notes": None,
        "process_description": None,
        "problem_description": None,
        "improvement_description": None,
        "expected_result": None,
        "category": None,
        "current_revision_number": 1,
        "created_by_user_id": "u1",
        "updated_by_user_id": "u1",
        "created_at": date(2026, 6, 15),
        "updated_at": date(2026, 6, 15),
    }
    base.update(overrides)
    return base


def test_summary_keeps_period_savings_and_active_when_no_new_implants_in_period() -> None:
    repo = PostgresKaizenRepository()
    repo.fetch_all = MagicMock(return_value=[_implanted_row()])

    result = repo.summary(
        branch_code="01",
        date_start="2026-07-01",
        date_end="2026-07-03",
    )

    assert result["total"] == 0
    assert result["period_implanted_count"] == 0
    assert result["period_savings"] > 0
    assert result["active_count"] == 1
    assert result["active_annual_savings"] > 0
