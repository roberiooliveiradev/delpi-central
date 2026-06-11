"""Gate R23 — presentation builder com contexto de rota/perfil."""

from tests.fixtures.presentation_builder_items_table_gate import (
    validate_presentation_builder_items_table_context,
)


def test_presentation_builder_delegates_items_table_with_path():
    report = validate_presentation_builder_items_table_context()

    assert report["ok"] is True, "\n".join(report.get("violations") or [])
