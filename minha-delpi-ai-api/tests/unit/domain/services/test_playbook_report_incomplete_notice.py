from unittest.mock import MagicMock

from app.domain.services.external_actions.presenters.playbook_report_presenter import (
    ExternalActionPlaybookReportPresenter,
)


def test_playbook_report_presenter_surfaces_incomplete_notice() -> None:
    host = MagicMock()
    host._humanize_key.side_effect = lambda key: key
    host._format_field_value.side_effect = lambda key, value: str(value)
    host._presenter_text.side_effect = lambda *args, **values: args[1] if len(args) > 1 else ""

    presenter = ExternalActionPlaybookReportPresenter(host)
    root = {
        "summary": {
            "total_records": 50,
            "reference_date": "20260611",
            "branch": None,
            "branch_filter_applied": False,
            "is_complete": False,
        },
        "items": [{"product_code": "90261255", "description": "PRODUTO A"}],
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
    }

    result = presenter._present_playbook_report(
        root,
        "/production/schedule/today",
        entity="production_schedule_today",
    )

    assert result is not None
    assert "incompleteResultNoBranchFilter" in result["linhas"]
    assert "incompleteResultHint" in result["linhas"]
