from unittest.mock import MagicMock

from app.domain.services.external_actions.presenters.playbook_report_presenter import (
    ExternalActionPlaybookReportPresenter,
)


def test_playbook_report_presenter_does_not_embed_incomplete_notice() -> None:
    host = MagicMock()
    host._humanize_key.side_effect = lambda key: key
    host._format_field_value.side_effect = lambda key, value: str(value)
    host._presenter_text.side_effect = lambda *args, **values: args[1] if len(args) > 1 else ""
    host._build_items_table.return_value = {"type": "table", "rows": []}

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

    text_result = presenter._present_playbook_report(
        root,
        "/production/schedule/today",
        entity="production_schedule_today",
    )
    table_result = presenter._build_playbook_report_table(
        root,
        "/production/schedule/today",
        entity="production_schedule_today",
    )

    assert text_result is not None
    assert all("Resultado incompleto" not in line for line in text_result["linhas"])
    assert table_result is not None
    assert "incompleteNotice" not in table_result
