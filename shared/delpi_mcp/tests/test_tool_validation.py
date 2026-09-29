"""delpi_mcp wire validator tests — real-shape fixtures from VISTA/TÉO/DAVI.

Fixtures below mirror the serialized ``types.Tool.model_dump(
mode="json", by_alias=True)`` output observed in production code review —
not invented shapes.
"""

from __future__ import annotations

import pytest

from delpi_mcp.tool_validation import (
    ValidationLayer,
    validate_tool_wire,
    validate_tools_wire,
)


def _vista_tool() -> dict:
    """VISTA mcp 2.x wire shape: namespaced delpi/* metadata."""
    return {
        "name": "list_playlists",
        "title": "Listar programações do usuário",
        "description": "Lista as programações do TV Dashboard.",
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": None,
        "annotations": {
            "title": "READ — tv-dashboard",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "icons": None,
        "execution": None,
        "_meta": {
            "delpi/securitySchemes": ["Authorization Code", "Bearer OAuth"],
            "delpi/toolClass": "READ",
        },
    }


def _teo_tool() -> dict:
    """TÉO mcp 1.x wire shape: reserved _meta.securitySchemes typed objects
    plus the OpenAI top-level securitySchemes extension."""
    return {
        "name": "search_records",
        "title": "Search records",
        "description": "Search Transformômetro records.",
        "inputSchema": {"type": "object", "properties": {"entity": {"type": "string"}}},
        "outputSchema": None,
        "annotations": {
            "title": "Search records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        "icons": None,
        "_meta": {
            "securitySchemes": [
                {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
            ]
        },
        "securitySchemes": [
            {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
        ],
    }


def _davi_tool() -> dict:
    """DAVI mcp 1.x wire shape: same reserved _meta + top-level promotion,
    plus a real outputSchema."""
    return {
        "name": "discover_delpi_information",
        "title": "Discover DELPI information",
        "description": "Find the governed DELPI READ capability.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "title": "Discover DELPI information",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        "icons": None,
        "_meta": {
            "securitySchemes": [
                {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
            ]
        },
        "securitySchemes": [
            {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
        ],
    }


# --- positive: all three production strategies validate --------------------


@pytest.mark.parametrize("factory", [_vista_tool, _teo_tool, _davi_tool])
def test_all_current_metadata_strategies_validate(factory):
    issues = validate_tool_wire(factory(), profile="openai")
    assert issues == [], [f"{i.layer.value}:{i.code}:{i.path}" for i in issues]


def test_vista_tool_core_profile_clean():
    issues = validate_tool_wire(_vista_tool(), profile="core")
    assert issues == []


def test_teo_top_level_security_schemes_flagged_under_core():
    """Top-level securitySchemes is an OpenAI extension — flagged in core."""
    issues = validate_tool_wire(_teo_tool(), profile="core")
    codes = {i.code for i in issues}
    assert "TOOL_UNKNOWN_TOP_LEVEL_FIELD" in codes


# --- negative: VISTA incident 1 — string securitySchemes -------------------


def test_vista_historical_string_security_schemes_rejected():
    """Regression: _meta.securitySchemes=[str] broke ChatGPT discovery."""
    tool = _vista_tool()
    tool["_meta"] = {"securitySchemes": ["openid", "profile", "email", "mcp:tools"]}
    issues = validate_tool_wire(tool, profile="core")
    codes = {i.code for i in issues}
    assert "RESERVED_META_SECURITY_SCHEMES_INVALID" in codes
    layers = {i.layer for i in issues if i.code == "RESERVED_META_SECURITY_SCHEMES_INVALID"}
    assert layers == {ValidationLayer.MCP_STANDARD}


def test_bare_unknown_meta_key_rejected_by_policy():
    tool = _vista_tool()
    tool["_meta"] = {"customFlag": True}
    issues = validate_tool_wire(tool, profile="core")
    codes = {i.code for i in issues}
    assert "DELPI_META_UNNAMESPACED_KEY" in codes
    issue = next(i for i in issues if i.code == "DELPI_META_UNNAMESPACED_KEY")
    assert issue.layer is ValidationLayer.DELPI_POLICY


def test_delpi_namespaced_metadata_accepted():
    tool = _vista_tool()
    tool["_meta"]["delpi/customThing"] = {"anything": [1, 2]}
    assert validate_tool_wire(tool, profile="core") == []


def test_other_namespaced_meta_tolerated():
    tool = _vista_tool()
    tool["_meta"]["mcp/www_authenticate"] = ["Bearer realm=x"]
    assert validate_tool_wire(tool, profile="core") == []


def test_meta_not_object_rejected():
    tool = _vista_tool()
    tool["_meta"] = "not-a-map"
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "META_NOT_OBJECT" in codes


# --- negative: schema/name/serialization -----------------------------------


def test_duplicate_tool_names_rejected():
    t = _vista_tool()
    issues = validate_tools_wire([t, dict(t)])
    assert any(i.code == "TOOL_NAME_DUPLICATE" for i in issues)


def test_invalid_input_schema_rejected():
    tool = _vista_tool()
    tool["inputSchema"] = "not-an-object"
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "TOOL_SCHEMA_INVALID" in codes


def test_input_schema_non_object_type_rejected():
    tool = _vista_tool()
    tool["inputSchema"] = {"type": "array"}
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "TOOL_INPUT_SCHEMA_NOT_OBJECT" in codes


def test_missing_name_rejected():
    tool = _vista_tool()
    del tool["name"]
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "TOOL_NAME_MISSING" in codes


def test_non_serializable_meta_rejected():
    tool = _vista_tool()
    tool["_meta"] = {"delpi/bad": {"x": object()}}
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "META_NOT_SERIALIZABLE" in codes


def test_annotation_hint_wrong_type_rejected():
    tool = _vista_tool()
    tool["annotations"]["readOnlyHint"] = "yes"
    codes = {i.code for i in validate_tool_wire(tool, profile="core")}
    assert "ANNOTATION_HINT_TYPE_INVALID" in codes


# --- OpenAI profile field requirements --------------------------------------


def test_openai_profile_requires_scheme_type_and_scopes():
    tool = _teo_tool()
    tool["_meta"] = {"securitySchemes": [{"type": "oauth2"}]}  # scopes missing
    issues = validate_tool_wire(tool, profile="openai")
    assert any(
        i.layer is ValidationLayer.OPENAI_COMPATIBILITY
        and i.code == "OPENAI_SECURITY_SCHEME_SCOPES_MISSING"
        for i in issues
    )


def test_openai_profile_skipped_under_core():
    tool = _teo_tool()
    tool["_meta"] = {"securitySchemes": [{"type": "oauth2"}]}
    issues = validate_tool_wire(tool, profile="core")
    assert not any(i.code.startswith("OPENAI_") for i in issues)
