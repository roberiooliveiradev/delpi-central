"""Unit tests for delpi_mcp.errors + tool_metadata — S5."""

from __future__ import annotations

import json

import pytest

mcp_types = pytest.importorskip("mcp.types")

from delpi_mcp.errors import (
    INTERNAL_ERROR_MESSAGE,
    json_payload_text,
    kind_for_http_status,
    mcp_tool_result,
    redact_error_details,
)
from delpi_mcp.tool_metadata import (
    DELPI_META_SECURITY_SCHEMES,
    DELPI_META_TOOL_CLASS,
    TOOL_CLASS_ACT,
    TOOL_CLASS_PREPARE,
    TOOL_CLASS_READ,
    delpi_tool_meta,
    security_schemes_meta,
    tool_annotations_payload,
)


# --- errors ---------------------------------------------------------------

def test_kind_for_http_status_vocabulary() -> None:
    assert kind_for_http_status(401) == "unauthenticated"
    assert kind_for_http_status(403) == "forbidden"
    assert kind_for_http_status(404) == "not_found"
    assert kind_for_http_status(409) == "conflict"
    assert kind_for_http_status(422) == "validation"
    assert kind_for_http_status(400) == "validation"
    assert kind_for_http_status(500) == "upstream"
    assert kind_for_http_status(502) == "upstream"
    assert kind_for_http_status(500, server_error="validation") == "validation"


def test_json_payload_text_safe() -> None:
    assert json_payload_text({"a": 1}) == '{"a": 1}'
    assert json_payload_text({"msg": "não"}) == '{"msg": "não"}'


def test_mcp_tool_result_success_with_structured() -> None:
    result = mcp_tool_result({"status": "success", "data": {"x": 1}}, is_error=False)
    assert json.loads(result.content[0].text) == {"status": "success", "data": {"x": 1}}
    dumped = result.model_dump(mode="json", by_alias=True)
    assert dumped["structuredContent"] == {"status": "success", "data": {"x": 1}}
    assert dumped["isError"] is False


def test_mcp_tool_result_error_with_meta() -> None:
    meta = {"mcp/www_authenticate": 'Bearer realm="x"'}
    result = mcp_tool_result(
        {"code": "AUTHENTICATION_REQUIRED", "message": "nope"},
        is_error=True,
        meta=meta,
    )
    dumped = result.model_dump(mode="json", by_alias=True)
    assert dumped["isError"] is True
    assert dumped["_meta"] == meta
    assert dumped["structuredContent"]["code"] == "AUTHENTICATION_REQUIRED"


def test_mcp_tool_result_text_only() -> None:
    result = mcp_tool_result(is_error=True, text="Forbidden")
    dumped = result.model_dump(mode="json", by_alias=True)
    assert dumped["isError"] is True
    assert dumped["content"][0]["text"] == "Forbidden"
    assert "structuredContent" not in dumped or dumped.get("structuredContent") in (
        None,
        {},
    )


def test_redact_error_details_drops_secrets() -> None:
    details = {
        "field": "name",
        "access_token": "abc",
        "Authorization": "Bearer x",
        "clientSecret": "s",
        "retry_after": 5,
    }
    safe = redact_error_details(details)
    assert safe == {"field": "name", "retry_after": 5}


def test_redact_error_details_none_when_all_secret() -> None:
    assert redact_error_details({"token": "x", "password": "y"}) is None
    assert redact_error_details(None) is None
    assert redact_error_details({}) is None


def test_error_is_not_empty_contract() -> None:
    # An error result always carries a payload or explicit text — never {}.
    result = mcp_tool_result({"code": "INTERNAL", "message": INTERNAL_ERROR_MESSAGE}, is_error=True)
    assert result.content[0].text != "{}"


# --- tool metadata --------------------------------------------------------

def test_tool_annotations_payload_wire_keys() -> None:
    payload = tool_annotations_payload(
        "READ — app", read_only=True, destructive=False, idempotent=True
    )
    assert payload == {
        "title": "READ — app",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }


def test_tool_annotations_payload_omits_unset_idempotent() -> None:
    payload = tool_annotations_payload("T", read_only=False, destructive=True)
    assert "idempotentHint" not in payload


def test_delpi_tool_meta_namespaced() -> None:
    schemes = [{"type": "oauth2", "scopes": ["openid"]}]
    meta = delpi_tool_meta(tool_class=TOOL_CLASS_READ, security_schemes=schemes)
    assert meta[DELPI_META_TOOL_CLASS] == "READ"
    assert meta[DELPI_META_SECURITY_SCHEMES] == schemes
    assert "securitySchemes" not in meta


def test_security_schemes_meta_reserved_key() -> None:
    schemes = [{"type": "oauth2", "scopes": ["mcp:tools"]}]
    assert security_schemes_meta(schemes) == {"securitySchemes": schemes}


def test_tool_class_vocabulary_frozen() -> None:
    for klass in (TOOL_CLASS_READ, TOOL_CLASS_PREPARE, TOOL_CLASS_ACT):
        assert klass in {"READ", "ANALYSIS", "PREPARE", "ACT"}
