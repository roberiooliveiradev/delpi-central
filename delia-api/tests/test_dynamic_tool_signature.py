"""Dynamic Pydantic AI tool signature generation from owner schemas.

Covers the contract introduced for the real-READ closure: every owner
capability gets a native tool whose parameters mirror the owner
``input_schema`` — never a generic ``arguments`` envelope. Schemas are
untrusted owner data: property order is not a contract, names may
collide with internals, and malformed shapes must fail closed to the
``arguments`` escape hatch instead of breaking toolset registration.
"""

from __future__ import annotations

import inspect
import json
from typing import Any

from pydantic_ai.tools import Tool

from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _capability_tool_signature,
)


def _tool_json_schema(input_schema):
    def owner_tool(ctx, **kwargs):  # pragma: no cover - schema carrier
        return "ok"

    owner_tool.__signature__ = _capability_tool_signature(input_schema)
    owner_tool.__annotations__ = {
        p.name: (
            p.annotation
            if p.annotation is not inspect.Parameter.empty
            else Any  # noqa: F821
        )
        for p in owner_tool.__signature__.parameters.values()
    }
    owner_tool.__annotations__["return"] = str
    tool = Tool(function=owner_tool, takes_ctx=True, name="cap_x")
    return tool.function_schema.json_schema


def _params(input_schema):
    return _capability_tool_signature(input_schema).parameters


class TestParameterOrdering:
    def test_optional_before_required_builds_valid_signature(self):
        # JSON Schema carries no ordering contract — an optional
        # property listed first must not break signature construction.
        schema = {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "code": {"type": "string"},
            },
            "required": ["code"],
        }
        params = _params(schema)
        assert params["code"].default is inspect.Parameter.empty
        assert params["page"].default is None
        json_schema = _tool_json_schema(schema)
        assert json_schema["required"] == ["code"]
        assert set(json_schema["properties"]) >= {"code", "page"}

    def test_all_schema_params_are_keyword_only(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
            "required": ["a"],
        }
        params = _params(schema)
        assert params["ctx"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in ("a", "b", "arguments"):
            assert (
                params[name].kind is inspect.Parameter.KEYWORD_ONLY
            ), name


class TestTypeMatrix:
    def test_scalar_and_container_types(self):
        schema = {
            "type": "object",
            "properties": {
                "s": {"type": "string"},
                "i": {"type": "integer"},
                "n": {"type": "number"},
                "b": {"type": "boolean"},
                "o": {"type": "object"},
                "a": {"type": "array"},
            },
            "required": ["s", "i", "n", "b", "o", "a"],
        }
        json_schema = _tool_json_schema(schema)
        props = json_schema["properties"]
        assert props["s"]["type"] == "string"
        assert props["i"]["type"] == "integer"
        assert props["n"]["type"] == "number"
        assert props["b"]["type"] == "boolean"
        assert props["o"]["type"] == "object"
        assert props["a"]["type"] == "array"

    def test_nested_object_property_stays_object(self):
        schema = {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}},
                }
            },
            "required": ["filter"],
        }
        json_schema = _tool_json_schema(schema)
        assert json_schema["properties"]["filter"]["type"] == "object"
        assert json_schema["required"] == ["filter"]

    def test_unknown_type_falls_back_to_any(self):
        schema = {
            "type": "object",
            "properties": {"weird": {"type": "custom-thing"}},
            "required": ["weird"],
        }
        json_schema = _tool_json_schema(schema)
        assert "weird" in json_schema["properties"]
        assert json_schema["required"] == ["weird"]

    def test_enum_property_is_advertised(self):
        schema = {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["a", "b"]}
            },
            "required": ["mode"],
        }
        params = _params(schema)
        assert "mode" in params
        assert _tool_json_schema(schema)["required"] == ["mode"]

    def test_enum_values_reach_model_schema(self):
        # The model must see the allowed values — an unadvertised
        # enum makes it guess and the owner rejects the call.
        schema = {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "enum": ["transformer", "winding", "losses"],
                }
            },
            "required": ["entity"],
        }
        json_schema = _tool_json_schema(schema)
        prop = json_schema["properties"]["entity"]
        assert sorted(prop.get("enum", ())) == [
            "losses",
            "transformer",
            "winding",
        ]

    def test_oversized_enum_falls_back_to_type(self):
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": [f"v{i}" for i in range(80)],
                }
            },
        }
        params = _params(schema)
        assert params["code"].annotation is str


class TestUnsafeNames:
    def test_python_keywords_are_skipped(self):
        schema = {
            "type": "object",
            "properties": {
                "class": {"type": "string"},
                "for": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["query"],
        }
        params = _params(schema)
        assert "class" not in params
        assert "for" not in params
        assert params["query"].default is inspect.Parameter.empty

    def test_non_identifier_names_are_skipped(self):
        schema = {
            "type": "object",
            "properties": {
                "not a name": {"type": "string"},
                "1bad": {"type": "string"},
                "ok_name": {"type": "string"},
            },
        }
        params = _params(schema)
        assert "not a name" not in params
        assert "1bad" not in params
        assert "ok_name" in params

    def test_ctx_collision_is_denied(self):
        schema = {
            "type": "object",
            "properties": {
                "ctx": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["ctx", "query"],
        }
        params = _params(schema)
        # Only the RunContext receiver may be named ctx — the schema
        # property of the same name must not shadow it.
        assert list(params)[0] == "ctx"
        assert params["ctx"].annotation is inspect.Parameter.empty
        assert "query" in params

    def test_non_string_and_duplicate_names_bounded(self):
        schema = {
            "type": "object",
            "properties": {
                7: {"type": "string"},
                "ok": {"type": "string"},
            },
        }
        params = _params(schema)
        assert "ok" in params


class TestArgumentsEscapeHatch:
    def test_declared_arguments_becomes_named_param(self):
        schema = {
            "type": "object",
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {
                    "anyOf": [{"type": "object"}, {"type": "null"}]
                },
            },
            "required": ["candidate_token"],
        }
        params = _params(schema)
        assert params["candidate_token"].default is inspect.Parameter.empty
        assert "arguments" in params
        json_schema = _tool_json_schema(schema)
        assert json_schema["required"] == ["candidate_token"]

    def test_no_properties_keeps_arguments_bag(self):
        params = _params({"type": "object", "properties": {}})
        assert "arguments" in params

    def test_no_schema_keeps_arguments_bag(self):
        params = _params(None)
        assert "arguments" in params
        params = _params({"unexpected": "shape"})
        assert "arguments" in params

    def test_malformed_properties_falls_back(self):
        params = _params({"properties": "not-a-map"})
        assert "arguments" in params


class TestBounds:
    def test_property_cap_is_bounded(self):
        schema = {
            "type": "object",
            "properties": {
                f"p{i}": {"type": "string"} for i in range(40)
            },
        }
        params = _params(schema)
        advertised = [
            n for n in params if n not in {"ctx", "arguments"}
        ]
        assert len(advertised) == 24

    def test_json_schema_has_no_extra_required(self):
        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }
        json_schema = _tool_json_schema(schema)
        assert json_schema["required"] == ["query"]
        assert json_schema["type"] == "object"
        print(json.dumps(json_schema)[:400])
