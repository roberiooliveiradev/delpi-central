"""Response / OpenAPI budget gates for TÉO GPT Actions."""

from __future__ import annotations

from tm_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tm_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES,
    actions_response_sizes,
    project_catalog,
    project_search_records,
)


def test_search_projection_caps_items():
    payload = {
        "total": 100,
        "items": [{"id": i, "conteudo": "x" * 5000} for i in range(80)],
    }
    out = project_search_records(payload)
    assert out["truncated"] is True
    assert len(out["items"]) <= 40
    sizes = actions_response_sizes(out)
    assert sizes["envelopeAscii"] <= GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_catalog_projection_under_budget_when_bloated():
    bloated = {
        "entities": ["process"],
        "registration_guide": {
            "entity_schemas": {
                f"e{i}": {f"f{j}": "desc " * 200 for j in range(30)} for i in range(40)
            }
        },
        "diagram_catalog": {"nodes": [{"x": "y" * 1000} for _ in range(200)]},
        "capability_surface": {"agent_directives": {"version": "1", "flows": {}}},
        "familias_processo": ["a"] * 500,
    }
    out = project_catalog(bloated)
    sizes = actions_response_sizes(out)
    assert sizes["envelopeAscii"] <= GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_openapi_artifact_budget_and_op_count():
    import json
    from pathlib import Path

    doc = build_gpt_actions_openapi(server_url="https://example.test")
    raw = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(raw) <= GPT_ACTIONS_RESPONSE_MAX_BYTES, len(raw)
    ops = []
    for methods in doc.get("paths", {}).values():
        if not isinstance(methods, dict):
            continue
        for op in methods.values():
            if isinstance(op, dict) and op.get("operationId"):
                ops.append(op["operationId"])
    assert len(ops) == 18

    artifact = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "gpt-actions"
        / "openapi-gpt-actions.json"
    )
    if artifact.exists():
        assert artifact.stat().st_size <= GPT_ACTIONS_RESPONSE_MAX_BYTES
