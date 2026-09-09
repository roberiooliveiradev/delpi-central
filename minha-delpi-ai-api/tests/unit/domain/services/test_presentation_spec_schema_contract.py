"""Contract: PresentationSpec JSON Schema is closed (additionalProperties false)."""

from app.domain.entities.presentation_spec import (
    PRESENTATION_INTENT_JSON_SCHEMA,
    PRESENTATION_SPEC_JSON_SCHEMA,
)


def test_presentation_spec_schema_is_closed():
    assert PRESENTATION_SPEC_JSON_SCHEMA["additionalProperties"] is False
    assert PRESENTATION_SPEC_JSON_SCHEMA["required"] == ["version", "view"]
    encoding = PRESENTATION_SPEC_JSON_SCHEMA["properties"]["encoding"]
    assert encoding["additionalProperties"] is False


def test_presentation_intent_schema_is_closed():
    assert PRESENTATION_INTENT_JSON_SCHEMA["additionalProperties"] is False
