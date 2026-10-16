"""PROPOSAL PROBE — presentation.v2 contract validation.

DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R2 / doc 84 §2/§2.5/§2.9.

Validates the PROPOSED schema artifact mechanically — the schema is
NOT active in any runtime. Two layers are exercised:

1. ``contracts/presentation-v2.proposal.schema.json`` is evaluated
   against positive/negative payloads with a bounded subset evaluator
   (below). The authoritative validation was ALSO executed with the
   real ``jsonschema`` package (Draft 2020-12, 22/22 — doc 86 §E.1);
   this file keeps the checks reproducible inside the repo without
   adding a dependency to the service requirements.

2. The proposed consumer decision table (doc 84 §2.5 / R2-02) is
   executed as a pure function so the fallback matrix is executable
   evidence — not prose. It is a POLICY probe; the real consumer does
   not exist yet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "docs/12-roadmap-e-evolucao/delia/contracts/"
    "presentation-v2.proposal.schema.json"
)

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Minimal evaluator for the subset of JSON Schema used by the artifact:
# const / enum / type (+nullable) / required / properties /
# additionalProperties / maxLength / minItems / maxItems / uniqueItems /
# oneOf / $ref to $defs. Enough to mechanically check this proposal —
# NOT a general Draft 2020-12 implementation.
# ---------------------------------------------------------------------------

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "null": lambda v: v is None,
    "boolean": lambda v: isinstance(v, bool),
}


def _resolve(node: dict) -> dict:
    ref = node.get("$ref")
    if not ref:
        return node
    assert ref.startswith("#/$defs/")
    return {**schema["$defs"][ref.split("/")[-1]], **{k: v for k, v in node.items() if k != "$ref"}}


def _valid(node: dict, value: object) -> bool:
    node = _resolve(node)
    if "oneOf" in node:
        return sum(1 for s in node["oneOf"] if _valid(s, value)) == 1
    if "const" in node:
        return value == node["const"]
    if "type" in node:
        types = node["type"] if isinstance(node["type"], list) else [node["type"]]
        if not any(_TYPE_CHECKS[t](value) for t in types):
            return False
    if "enum" in node and value not in node["enum"]:
        return False
    if isinstance(value, dict):
        required = node.get("required", [])
        if any(k not in value for k in required):
            return False
        props = node.get("properties", {})
        if node.get("additionalProperties") is False:
            if any(k not in props for k in value):
                return False
        for key, sub in props.items():
            if key in value and not _valid(sub, value[key]):
                return False
    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            return False
        if "maxItems" in node and len(value) > node["maxItems"]:
            return False
        if node.get("uniqueItems") and len({json.dumps(i, sort_keys=True) for i in value}) != len(value):
            return False
        if "items" in node and not all(_valid(node["items"], i) for i in value):
            return False
    if isinstance(value, str) and "maxLength" in node and len(value) > node["maxLength"]:
        return False
    return True


BASE = {
    "version": "2",
    "message_kind": "RESULT",
    "semantic_status": "OBSERVATION",
    "grounding_status": "GROUNDED",
    "allowed_interactions": ["reply"],
}


def _payload(**over):
    out = {**BASE, "blocks": [{"kind": "text", "format": "plain", "text": "x"}]}
    out.update(over)
    return out


# --------------------------------------------------------------------------
# Schema probes
# --------------------------------------------------------------------------

POSITIVE = {
    "v2_plain": _payload(),
    "v2_markdown_safe": _payload(
        blocks=[{"kind": "text", "format": "markdown_safe", "text": "- OP-1\n- OP-2"}]
    ),
    "v2_text_plus_notice": _payload(
        message_kind="PRECONDITION_REQUIRED",
        semantic_status=None,
        blocks=[
            {"kind": "text", "format": "plain", "text": "Informe a filial."},
            {"kind": "notice", "role": "owner_hint", "text": "filial obrigatória"},
        ],
    ),
    "v2_confirmation_interactions": _payload(
        message_kind="CONFIRMATION_REQUIRED",
        allowed_interactions=["reply", "confirm", "reject"],
        blocks=[{"kind": "text", "format": "plain", "text": "Confirma?"}],
    ),
}

NEGATIVE = {
    "bad_version_v1": _payload(version="1"),
    "bad_version_absent": {k: v for k, v in _payload().items() if k != "version"},
    "unknown_version": _payload(version="9"),
    "missing_format": _payload(blocks=[{"kind": "text", "text": "x"}]),
    "bad_format_html": _payload(blocks=[{"kind": "text", "format": "html", "text": "<b>x</b>"}]),
    "bad_block_kind": _payload(blocks=[{"kind": "table", "format": "plain", "text": "x"}]),
    "extra_block_prop": _payload(blocks=[{"kind": "text", "format": "plain", "text": "x", "href": "javascript:alert(1)"}]),
    "extra_envelope_prop": _payload(evil=True),
    "empty_blocks": _payload(blocks=[]),
    "too_many_blocks": _payload(blocks=[{"kind": "text", "format": "plain", "text": "x"}] * 9),
    "oversize_text": _payload(blocks=[{"kind": "text", "format": "plain", "text": "x" * 16385}]),
    "bad_message_kind": _payload(message_kind="EVIL"),
    "bad_interaction": _payload(allowed_interactions=["execute"]),
    "bad_notice_role": _payload(blocks=[{"kind": "notice", "role": "link", "text": "x"}]),
    "notice_with_format": _payload(blocks=[{"kind": "notice", "role": "owner_hint", "format": "plain", "text": "x"}]),
    "bad_semantic_status": _payload(semantic_status="SOMETHING_ELSE"),
    "blocks_missing_text": _payload(blocks=[{"kind": "text", "format": "plain"}]),
}


@pytest.mark.parametrize("name", sorted(POSITIVE))
def test_v2_schema_positive(name: str) -> None:
    assert _valid(schema, POSITIVE[name]), name


@pytest.mark.parametrize("name", sorted(NEGATIVE))
def test_v2_schema_negative_fails_closed(name: str) -> None:
    assert not _valid(schema, NEGATIVE[name]), name


def test_v2_schema_rejects_non_object() -> None:
    assert not _valid(schema, "not-an-object")


# --------------------------------------------------------------------------
# R2-02 — consumer decision table (proposal policy, executable)
# --------------------------------------------------------------------------

LEGACY_SAFE = "legacy_safe"
LEGACY_UNSAFE = "legacy_unsafe"


def _legacy_ok(legacy: dict) -> bool:
    content = legacy.get("content")
    return isinstance(content, str) and len(content) <= 16_384


def resolve_presentation(result: dict) -> str:
    """Proposed consumer decision — doc 84 §2.5 (executable probe).

    Returns the resolution kind the MFE MUST apply. Unknown/absent
    versions NEVER reach v2 semantics: the legacy `content` field is
    validated first; only a safe legacy projection is rendered.
    Structurally invalid or non-adherent v2 payloads are fail-closed
    errors — never silently downgraded. Rendering failures over
    already-admitted markdown degrade to inert text, not to an error.
    """
    presentation = result.get("presentation")
    version = presentation.get("version") if isinstance(presentation, dict) else None
    if version != "2":
        return "render_legacy" if _legacy_ok(result) else "neutral_error"
    if not _valid(schema, presentation):
        return "neutral_error"
    for block in presentation["blocks"]:
        if block["kind"] == "text" and block["format"] == "markdown_safe":
            try:
                _parse_markdown_safe(block["text"])
            except MarkdownParseFailure:
                return "inert_text"
    return "render_v2"


class MarkdownParseFailure(Exception):
    pass


def _parse_markdown_safe(text: str) -> None:
    """Stand-in for the future renderer parse — fails on unbalanced
    fenced code to exercise the render-failure branch."""
    if text.count("```") % 2 != 0:
        raise MarkdownParseFailure("unbalanced fence")


def _result(presentation=None, content="ok"):
    return {"content": content, "presentation": presentation}


def test_fallback_v1_result_renders_legacy() -> None:
    assert resolve_presentation(_result(presentation={"version": "1"})) == "render_legacy"


def test_fallback_absent_version_renders_legacy_when_safe() -> None:
    assert resolve_presentation(_result(presentation=None)) == "render_legacy"


def test_fallback_unknown_version_renders_legacy_when_safe() -> None:
    assert resolve_presentation(_result(presentation={"version": "9"})) == "render_legacy"


def test_fallback_unknown_version_and_unsafe_legacy_is_neutral_error() -> None:
    result = _result(presentation={"version": "9"}, content=12345)
    assert resolve_presentation(result) == "neutral_error"


def test_fallback_v2_schema_invalid_is_neutral_error_not_downgrade() -> None:
    result = _result(presentation={**BASE, "blocks": [{"kind": "text", "format": "html", "text": "<b>x</b>"}]})
    assert resolve_presentation(result) == "neutral_error"


def test_fallback_v2_extra_properties_are_neutral_error_not_legacy_downgrade() -> None:
    """R3-03: additionalProperties reject → neutral_error (not legacy fallback)."""
    result = _result(
        presentation={
            **BASE,
            "blocks": [
                {
                    "kind": "text",
                    "format": "plain",
                    "text": "safe-looking",
                    "href": "https://evil.example",
                }
            ],
        },
        content="legacy plain must NOT be used for structurally invalid v2",
    )
    assert resolve_presentation(result) == "neutral_error"


def test_fallback_v2_missing_format_is_neutral_error() -> None:
    result = _result(presentation={**BASE, "blocks": [{"kind": "text", "text": "x"}]})
    assert resolve_presentation(result) == "neutral_error"


def test_fallback_v2_render_failure_on_admitted_content_is_inert_text() -> None:
    result = _result(
        presentation={
            **BASE,
            "blocks": [{"kind": "text", "format": "markdown_safe", "text": "```python\nx = 1"}],
        }
    )
    assert resolve_presentation(result) == "inert_text"


def test_fallback_v2_valid_markdown_safe_renders_v2() -> None:
    result = _result(
        presentation={
            **BASE,
            "blocks": [{"kind": "text", "format": "markdown_safe", "text": "- OP-1\n- OP-2"}],
        }
    )
    assert resolve_presentation(result) == "render_v2"
