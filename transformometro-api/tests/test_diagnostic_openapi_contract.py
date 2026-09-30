"""Diagnostic Portal HTTP — OpenAPI registration contract.

Proves the canonical test app — the same app that generates
``openapi_baseline.json`` and feeds ``audit_route_test_coverage.py`` —
exposes exactly the five Diagnostic Portal operationIds mounted in
production by ``tm_app.main``. This is the internal Portal surface; it is
unrelated to the GPT Actions generated contract.
"""

from __future__ import annotations

from tests.support.test_app import create_test_app

EXPECTED_OPERATIONS = {
    (
        "GET",
        "/transformometro/revisions/{revision_id}/diagnostics",
    ): "list_diagnostics_by_revision",
    (
        "GET",
        "/transformometro/diagnostics/{diagnostic_id}",
    ): "get_diagnostic",
    (
        "POST",
        "/transformometro/revisions/{revision_id}/diagnostics/prepare",
    ): "prepare_create_diagnostic",
    (
        "POST",
        "/transformometro/diagnostics/{diagnostic_id}/prepare",
    ): "prepare_manage_diagnostic",
    (
        "POST",
        "/transformometro/governed-proposals/commit",
    ): "commit_governed_proposal",
}


def test_diagnostic_portal_operations_registered_in_test_app_schema() -> None:
    schema = create_test_app().openapi()
    actual = {
        (method.upper(), path): op.get("operationId")
        for path, methods in (schema.get("paths") or {}).items()
        if isinstance(methods, dict)
        for method, op in methods.items()
        if isinstance(op, dict)
    }
    for (method, path), operation_id in EXPECTED_OPERATIONS.items():
        assert actual.get((method, path)) == operation_id, (
            f"{method} {path} ausente ou operationId divergente "
            f"(esperado {operation_id})"
        )
