"""TÉO GPT Builder typed package projections and explicit domain-context exception."""
import json
from pathlib import Path
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi, count_operations, GPT_ACTIONS_OPERATION_IDS,
)

_ARTIFACT = Path(__file__).resolve().parents[1] / "docs/gpt-actions/openapi-gpt-actions.json"


def test_governed_package_uses_typed_canonical_shapes():
    schemas = build_gpt_actions_openapi()["components"]["schemas"]
    source = schemas["GptImprovementPackageBody"]["properties"]
    target = schemas["GptGovernedOperationBody"]["properties"]
    for field in ("process", "instance", "baseline", "scenario"):
        assert target[field] == source[field], field
        assert target[field]["properties"], field
    assert target["baseline"]["additionalProperties"] is False
    assert target["scenario"]["additionalProperties"] is False


def test_context_is_intentional_domain_validated_opaque_shape():
    schemas = build_gpt_actions_openapi()["components"]["schemas"]
    for name, field in (("GptRecordBody", "data"), ("GptPrepareRecordChangeBody", "changes")):
        context = schemas[name]["properties"][field]["properties"]["contexto"]
        assert context["type"] == "object"
        assert context["additionalProperties"] is True
        assert context["x-delpi-gpt-opaque-object"] is True
        assert "canonical domain validator" in context["description"]


def test_static_artifact_parity_and_budget():
    doc = build_gpt_actions_openapi()
    assert json.loads(_ARTIFACT.read_text(encoding="utf-8")) == doc
    assert len(_ARTIFACT.read_bytes()) <= 100 * 1024
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS) == 21
