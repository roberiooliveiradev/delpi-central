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


def test_openapi_has_no_type_unions_for_builder():
    """GPT Builder rejects OAS 3.1 type: [string, null] / Python None tokens."""
    doc = build_gpt_actions_openapi()

    bad: list[str] = []

    def walk(obj: object, path: str = "") -> None:
        if isinstance(obj, dict):
            t = obj.get("type")
            if isinstance(t, list):
                bad.append(f"{path}: {t}")
            if t in (None, "None") and "type" in obj:
                # bare invalid token
                bad.append(f"{path}: type={t!r}")
            for key, value in obj.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                walk(value, f"{path}[{index}]")

    walk(doc)
    assert not bad, bad

    fim = doc["components"]["schemas"]["GptRecordBody"]["properties"]["data"][
        "properties"
    ]["data_fim_vigencia"]
    assert fim["type"] == "string"
    assert fim.get("nullable") is True
