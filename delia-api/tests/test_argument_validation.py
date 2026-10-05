"""ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03R1 — bounded
schema-aware argument-instance validation.

Covers the deterministic contract of
``app/application/interaction/argument_validation.py``:

- JSON-string normalization (DEFECT-1)
- nested schema-aware values (DEFECT-2)
- fail-closed bounds, unknown fields, required fields
- orchestration-owned field injection (top-level, nested, stringified)
"""

import json

import pytest

from app.application.interaction.argument_validation import (
    MAX_ARGUMENT_ARRAY_ITEMS,
    MAX_ARGUMENT_DEPTH,
    MAX_ARGUMENT_NODES,
    MAX_ARGUMENT_OBJECT_KEYS,
    MAX_ARGUMENT_SERIALIZED_BYTES,
    MAX_ARGUMENT_STRING_CHARS,
    MAX_TOP_LEVEL_KEYS,
    normalize_arguments,
    validate_arguments,
    validate_untyped_arguments,
)


# --- primitive value matrix ----------------------------------------------


def _typed_schema(**prop):
    return {"type": "object", "properties": prop}


@pytest.mark.parametrize(
    "prop_schema,value",
    [
        ({"type": "string"}, "texto"),
        ({"type": "integer"}, 42),
        ({"type": "number"}, 3.14),
        ({"type": "number"}, 7),
        ({"type": "boolean"}, True),
        ({"type": "boolean"}, False),
        ({"type": ["string", "null"]}, None),
    ],
)
def test_primitives_accepted(prop_schema, value):
    schema = _typed_schema(field=prop_schema)
    assert validate_arguments({"field": value}, schema) == {
        "field": value
    }


@pytest.mark.parametrize(
    "prop_schema,value",
    [
        ({"type": "string"}, 42),
        ({"type": "integer"}, "42"),
        ({"type": "integer"}, True),  # bool is not an integer
        ({"type": "number"}, "3.14"),
        ({"type": "boolean"}, "true"),
        ({"type": "object"}, "not-an-object"),
        ({"type": "array"}, {"a": 1}),
        ({"type": ["string"]}, None),
    ],
)
def test_wrong_types_rejected(prop_schema, value):
    schema = _typed_schema(field=prop_schema)
    assert validate_arguments({"field": value}, schema) is None


# --- nested structures ----------------------------------------------------


def test_nested_object_two_levels():
    schema = _typed_schema(
        changes={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "detail": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}},
                },
            },
            "required": ["name"],
        }
    )
    args = {"changes": {"name": "X", "detail": {"code": "c1"}}}
    assert validate_arguments(args, schema) == args


def test_array_of_primitives():
    schema = _typed_schema(
        tags={"type": "array", "items": {"type": "string"}}
    )
    assert validate_arguments({"tags": ["a", "b"]}, schema) == {
        "tags": ["a", "b"]
    }
    assert validate_arguments({"tags": ["a", 1]}, schema) is None


def test_array_of_objects():
    schema = _typed_schema(
        ops={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"field": {"type": "string"}},
                "required": ["field"],
            },
        }
    )
    args = {"ops": [{"field": "a"}, {"field": "b"}]}
    assert validate_arguments(args, schema) == args
    bad = {"ops": [{"field": "a"}, {"other": 1}]}
    assert validate_arguments(bad, schema) is None


def test_nested_array_and_object_containing_array():
    schema = _typed_schema(
        matrix={"type": "array", "items": {"type": "array"}},
        payload={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "integer"}}
            },
        },
    )
    args = {"matrix": [[1, 2], [3]], "payload": {"items": [1, 2, 3]}}
    assert validate_arguments(args, schema) == args


def test_array_of_objects_containing_arrays():
    schema = _typed_schema(
        rows={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cells": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
            },
        }
    )
    args = {"rows": [{"cells": ["a", "b"]}, {"cells": []}]}
    assert validate_arguments(args, schema) == args


# --- enum / const / numeric-string bounds ---------------------------------


def test_enum_and_const():
    schema = _typed_schema(
        action={"enum": ["create", "update", "delete"]},
        kind={"const": "record"},
    )
    assert validate_arguments(
        {"action": "update", "kind": "record"}, schema
    ) == {"action": "update", "kind": "record"}
    assert (
        validate_arguments(
            {"action": "drop", "kind": "record"}, schema
        )
        is None
    )
    assert (
        validate_arguments(
            {"action": "update", "kind": "other"}, schema
        )
        is None
    )


def test_string_and_numeric_schema_bounds():
    schema = _typed_schema(
        code={"type": "string", "minLength": 2, "maxLength": 5},
        qty={"type": "integer", "minimum": 1, "maximum": 10},
    )
    assert validate_arguments(
        {"code": "abc", "qty": 5}, schema
    ) == {"code": "abc", "qty": 5}
    assert validate_arguments({"code": "a", "qty": 5}, schema) is None
    assert (
        validate_arguments({"code": "abcdef", "qty": 5}, schema)
        is None
    )
    assert validate_arguments({"code": "abc", "qty": 0}, schema) is None
    assert (
        validate_arguments({"code": "abc", "qty": 11}, schema) is None
    )


def test_array_schema_bounds():
    schema = _typed_schema(
        ids={"type": "array", "minItems": 1, "maxItems": 3}
    )
    assert validate_arguments({"ids": [1, 2]}, schema) == {"ids": [1, 2]}
    assert validate_arguments({"ids": []}, schema) is None
    assert (
        validate_arguments({"ids": [1, 2, 3, 4]}, schema) is None
    )


def test_anyof_branch():
    schema = _typed_schema(
        target={
            "anyOf": [
                {"type": "object", "required": ["id"]},
                {"type": "null"},
            ]
        }
    )
    assert validate_arguments({"target": {"id": "x"}}, schema) == {
        "target": {"id": "x"}
    }
    assert validate_arguments({"target": None}, schema) == {
        "target": None
    }
    assert validate_arguments({"target": 5}, schema) is None


# --- unknown / additional fields -------------------------------------------


def test_unknown_top_level_property_rejected():
    schema = _typed_schema(name={"type": "string"})
    assert (
        validate_arguments({"name": "x", "invented": 1}, schema)
        is None
    )


def test_nested_unknown_rejected_when_additional_properties_false():
    schema = _typed_schema(
        changes={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
    )
    assert (
        validate_arguments(
            {"changes": {"name": "x", "extra": 1}}, schema
        )
        is None
    )


def test_nested_unknown_allowed_when_owner_permits():
    """Owner business payloads with additionalProperties absent/true
    pass bounded — the owner stays the final validator."""
    schema = _typed_schema(
        changes={
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
    )
    args = {"changes": {"name": "x", "custom_field": 1}}
    assert validate_arguments(args, schema) == args


def test_additional_properties_schema_enforced():
    schema = _typed_schema(
        labels={
            "type": "object",
            "additionalProperties": {"type": "string"},
        }
    )
    assert validate_arguments(
        {"labels": {"a": "x"}}, schema
    ) == {"labels": {"a": "x"}}
    assert (
        validate_arguments({"labels": {"a": 1}}, schema) is None
    )


# --- required fields --------------------------------------------------------


def test_missing_required_field_rejected():
    schema = {
        "type": "object",
        "properties": {"entity": {"type": "string"}},
        "required": ["entity"],
    }
    assert validate_arguments({}, schema) is None
    assert (
        validate_arguments({"other": "x"}, schema) is None
    )


def test_required_orchestrated_field_absent_still_valid():
    """candidate_token is required by the owner executor schema but is
    orchestration-resolved: its absence never invalidates the model
    proposal — the backend binds it later."""
    schema = {
        "type": "object",
        "properties": {
            "candidate_token": {"type": "string"},
            "arguments": {"type": "object"},
        },
        "required": ["candidate_token", "arguments"],
    }
    assert validate_arguments(
        {"arguments": {"description": "tubo"}}, schema
    ) == {"arguments": {"description": "tubo"}}


# --- orchestrated-field injection -------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "candidate_token",
        "proposal_handle",
        "confirmation",
        "idempotency_key",
        "commit_now",
    ],
)
def test_orchestrated_field_top_level_rejected(field):
    schema = _typed_schema(
        **{field: {"type": "string"}, "name": {"type": "string"}}
    )
    assert (
        validate_arguments({field: "x", "name": "y"}, schema) is None
    )


def test_orchestrated_field_stringified_injection_rejected():
    schema = _typed_schema(name={"type": "string"})
    raw = json.dumps(
        {"name": "x", "proposal_handle": "prop-handle-1"}
    )
    normalized = normalize_arguments(raw)
    assert normalized is not None
    assert validate_arguments(normalized, schema) is None


def test_nested_business_field_coincidental_name_allowed():
    """A nested business key named like an orchestrated field inside an
    owner-permitted payload is not blocked — the orchestration boundary
    is the top-level parameter list, not owner business data."""
    schema = _typed_schema(
        changes={"type": "object", "additionalProperties": True}
    )
    args = {"changes": {"confirmation": "valor de negocio"}}
    assert validate_arguments(args, schema) == args


# --- deterministic bounds ---------------------------------------------------


def _deep(depth):
    value = {"k": "leaf"}
    for _ in range(depth):
        value = {"k": value}
    return value


def test_max_depth_enforced():
    schema = _typed_schema(payload={"type": "object"})
    ok = {"payload": _deep(MAX_ARGUMENT_DEPTH - 2)}
    assert validate_arguments(ok, schema) == ok
    too_deep = {"payload": _deep(MAX_ARGUMENT_DEPTH + 2)}
    assert validate_arguments(too_deep, schema) is None


def test_max_array_items_enforced():
    schema = _typed_schema(ids={"type": "array"})
    over = {"ids": list(range(MAX_ARGUMENT_ARRAY_ITEMS + 1))}
    assert validate_arguments(over, schema) is None


def test_max_object_keys_enforced():
    schema = _typed_schema(payload={"type": "object"})
    over = {
        "payload": {
            f"k{i}": i for i in range(MAX_ARGUMENT_OBJECT_KEYS + 1)
        }
    }
    assert validate_arguments(over, schema) is None


def test_max_string_chars_enforced():
    schema = _typed_schema(text={"type": "string"})
    over = {"text": "x" * (MAX_ARGUMENT_STRING_CHARS + 1)}
    assert validate_arguments(over, schema) is None


def test_max_nodes_enforced():
    schema = _typed_schema(payload={"type": "array"})
    wide = {
        "payload": [
            {"a": 1, "b": 2, "c": 3} for _ in range(60)
        ]
    }
    # 60 objects * 4 nodes > MAX_ARGUMENT_NODES
    assert validate_arguments(wide, schema) is None


def test_max_top_level_keys_enforced():
    schema = {
        "type": "object",
        "properties": {
            f"k{i}": {"type": "integer"}
            for i in range(MAX_TOP_LEVEL_KEYS + 1)
        },
    }
    args = {f"k{i}": i for i in range(MAX_TOP_LEVEL_KEYS + 1)}
    assert validate_arguments(args, schema) is None


def test_max_serialized_bytes_enforced():
    schema = _typed_schema(a={"type": "string"}, b={"type": "string"})
    half = "x" * (MAX_ARGUMENT_SERIALIZED_BYTES // 2)
    args = {"a": half, "b": half}
    assert validate_arguments(args, schema) is None


def test_no_schema_accepts_only_empty():
    assert validate_arguments({}, None) == {}
    assert validate_arguments({"a": 1}, None) is None


# --- JSON-string normalization (DEFECT-1) -----------------------------------


def test_normalize_valid_json_object_string():
    raw = '{"changes":{"name":"X"}}'
    assert normalize_arguments(raw) == {"changes": {"name": "X"}}


@pytest.mark.parametrize(
    "raw",
    [
        "{invalid json",
        "[1,2,3]",
        '"scalar"',
        "42",
        'here is the JSON: {"a":1}',
        '{"a":1} trailing prose',
        "",
        "   ",
    ],
)
def test_normalize_rejects_non_object_strings(raw):
    assert normalize_arguments(raw) is None


def test_normalize_oversized_string_rejected():
    raw = "{" + '"a":"' + ("x" * MAX_ARGUMENT_SERIALIZED_BYTES) + '"}'
    assert normalize_arguments(raw) is None


def test_normalize_typed_mapping_verbatim():
    args = {"entity": "process", "changes": {"name": "X"}}
    assert normalize_arguments(args) == args


@pytest.mark.parametrize("raw", [[1, 2], 42, 3.14, True])
def test_normalize_rejects_non_mapping_non_string(raw):
    assert normalize_arguments(raw) is None


def test_normalize_none_is_empty_object():
    assert normalize_arguments(None) == {}


def test_stringified_valid_but_schema_invalid_rejected():
    """DEFECT-1 closure: string normalization is only the first gate —
    the parsed object still faces the owner schema."""
    schema = _typed_schema(entity={"type": "string"})
    normalized = normalize_arguments('{"wrong_key": "x"}')
    assert normalized is not None
    assert validate_arguments(normalized, schema) is None


def test_stringified_valid_end_to_end():
    schema = _typed_schema(
        entity={"type": "string"},
        changes={
            "type": "object",
            "properties": {"name": {"type": "string"}},
        },
    )
    raw = '{"entity":"process","changes":{"name":"X"}}'
    normalized = normalize_arguments(raw)
    assert validate_arguments(normalized, schema) == {
        "entity": "process",
        "changes": {"name": "X"},
    }


# --- schema-absent bounded path ---------------------------------------------


def test_untyped_arguments_bounded():
    assert validate_untyped_arguments({"a": 1, "b": {"c": [1]}}) == {
        "a": 1,
        "b": {"c": [1]},
    }
    assert validate_untyped_arguments(
        {"proposal_handle": "x"}
    ) is None
    deep = {"payload": _deep(MAX_ARGUMENT_DEPTH + 2)}
    assert validate_untyped_arguments(deep) is None
