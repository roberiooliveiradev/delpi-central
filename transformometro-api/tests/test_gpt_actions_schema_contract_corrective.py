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


def test_changed_imported_schemas_match_runtime_builder_and_budget():
    """Scoped parity for the exact five corrected schema fields.

    The full static import artifact has older unrelated drift; a full parity
    claim is not established by this test and requires a canonical sync.
    """
    generated = build_gpt_actions_openapi()
    imported = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    source = generated["components"]["schemas"]
    target = imported["components"]["schemas"]
    for field in ("process", "instance", "baseline", "scenario"):
        assert (
            target["GptGovernedOperationBody"]["properties"][field]
            == source["GptGovernedOperationBody"]["properties"][field]
        ), field
    for schema_name, field_name in (
        ("GptRecordBody", "data"),
        ("GptPrepareRecordChangeBody", "changes"),
    ):
        assert (
            target[schema_name]["properties"][field_name]["properties"]["contexto"]
            == source[schema_name]["properties"][field_name]["properties"]["contexto"]
        ), schema_name
    assert len(_ARTIFACT.read_bytes()) <= 100 * 1024
    assert count_operations(imported) == count_operations(generated) == len(GPT_ACTIONS_OPERATION_IDS) == 21
