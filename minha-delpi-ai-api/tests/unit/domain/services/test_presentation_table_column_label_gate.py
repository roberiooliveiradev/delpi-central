from tests.fixtures.presentation_table_column_label_gate import (
    validate_table_column_labels_for_ci,
)


def test_table_column_label_gate_is_green() -> None:
    report = validate_table_column_labels_for_ci()

    assert report["ok"] is True, report.get("tableColumnLabelGaps")
