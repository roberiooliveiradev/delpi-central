"""Gate R17 — zero caminho legado de colunas nos presenters."""

from tests.fixtures.presentation_legacy_table_columns_gate import (
    validate_no_legacy_table_columns_in_presenters,
)


def test_presenters_do_not_use_legacy_fixed_table_columns():
    report = validate_no_legacy_table_columns_in_presenters()

    assert report["ok"] is True, "\n".join(report.get("violations") or [])
