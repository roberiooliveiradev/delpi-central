"""Gate R22 — KV nos presenters com contexto de rota."""

from tests.fixtures.presentation_kv_label_context_gate import (
    validate_kv_label_context_in_presenters,
)


def test_presenters_pass_path_to_kv_label_helpers():
    report = validate_kv_label_context_in_presenters()

    assert report["ok"] is True, "\n".join(report.get("violations") or [])
