from __future__ import annotations

from si_app.application.services.strategic_indicators.measurement_errors import (
    has_stale_period_snapshot_errors,
)


def test_connection_refused_marks_period_snapshot_as_stale() -> None:
    errors = [
        {
            "department_id": "engineering",
            "source": "engineering_snapshot_consolidated",
            "message": "[Errno 111] Connection refused (competência 2026-05).",
        }
    ]
    assert has_stale_period_snapshot_errors(errors) is True


def test_clean_errors_are_not_stale() -> None:
    errors = [
        {
            "department_id": "financial",
            "source": "financial_snapshot",
            "message": "Valor ausente na planilha",
        }
    ]
    assert has_stale_period_snapshot_errors(errors) is False
