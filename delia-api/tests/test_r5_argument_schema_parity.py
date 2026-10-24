"""R5/M08 — schema/argument-completeness parity characterization.

Literal-output locks on the pure validation helpers R5 relocates to
``interaction/argument_validation.py``: required-gap dotted paths,
owner-declared defaults, entity-schema completeness and bounded caps.
Same inputs must produce the same outputs after the move.
"""

from __future__ import annotations

from app.application.interaction.argument_validation import (
    _apply_entity_defaults_to_arguments,
    _apply_owner_declared_defaults,
    _argument_completeness_gaps,
    _owner_entity_completeness_gaps,
    _schema_required_gaps,
)


SCHEMA = {
    "type": "object",
    "required": ["codigo", "endereco"],
    "properties": {
        "codigo": {"type": "string"},
        "endereco": {
            "type": "object",
            "required": ["rua"],
            "properties": {"rua": {"type": "string"}},
        },
    },
}


def test_required_gaps_dotted_paths_order():
    assert _schema_required_gaps({"codigo": "1"}, SCHEMA) == [
        "endereco"
    ]


def test_required_gaps_nested_inner_path():
    assert _schema_required_gaps(
        {"codigo": "1", "endereco": {}}, SCHEMA
    ) == ["endereco.rua"]


def test_required_gaps_none_is_missing():
    assert _schema_required_gaps(
        {"codigo": None, "endereco": {"rua": "x"}}, SCHEMA
    ) == ["codigo"]


def test_required_gaps_empty_string_is_missing():
    assert _schema_required_gaps(
        {"codigo": "  ", "endereco": {"rua": "x"}}, SCHEMA
    ) == ["codigo"]


def test_required_gaps_complete_schema_no_gaps():
    assert (
        _schema_required_gaps(
            {"codigo": "1", "endereco": {"rua": "a"}}, SCHEMA
        )
        == []
    )


def test_required_gaps_none_schema_no_gaps():
    assert _schema_required_gaps({"a": 1}, None) == []


def test_required_gaps_unknown_fields_ignored():
    assert _schema_required_gaps(
        {"codigo": "1", "endereco": {"rua": "a"}, "extra": True},
        SCHEMA,
    ) == []


def test_owner_defaults_fill_only_published_keys():
    filled = _apply_owner_declared_defaults(
        {"codigo": "1"},
        {"defaults": {"ativo": True, "filial": "01"}},
    )
    assert filled == {"codigo": "1", "ativo": True, "filial": "01"}


def test_owner_defaults_never_overwrite_declared_value():
    filled = _apply_owner_declared_defaults(
        {"ativo": False},
        {"defaults": {"ativo": True}},
    )
    assert filled == {"ativo": False}


def test_owner_defaults_without_defaults_returns_copy():
    payload = {"a": 1}
    out = _apply_owner_declared_defaults(payload, {})
    assert out == payload and out is not payload


def test_owner_defaults_no_invented_values():
    assert _apply_owner_declared_defaults(
        {"a": 1}, {"defaults": {}}
    ) == {"a": 1}


def _discovery(schemas):
    return {"entity_schemas": schemas}


def test_entity_completeness_gaps_inner_required():
    discovery = _discovery(
        {
            "item": {
                "required": ["codigo", "descricao"],
                "properties": {
                    "codigo": {"type": "string"},
                    "descricao": {"type": "string"},
                },
            }
        }
    )
    gaps = _owner_entity_completeness_gaps(
        {"entity": "item", "payload": {"codigo": "1"}}, discovery
    )
    assert gaps == ("descricao",)


def test_entity_completeness_gaps_defaults_resolve_gap():
    discovery = _discovery(
        {
            "item": {
                "required": ["codigo", "ativo"],
                "defaults": {"ativo": True},
                "properties": {"codigo": {}, "ativo": {}},
            }
        }
    )
    gaps = _owner_entity_completeness_gaps(
        {"entity": "item", "payload": {"codigo": "1"}}, discovery
    )
    assert gaps == ()


def test_entity_completeness_gaps_no_discovery_returns_empty():
    assert _owner_entity_completeness_gaps({"a": 1}, None) == ()


def test_entity_completeness_gaps_unknown_entity_returns_empty():
    discovery = _discovery({"other": {"required": ["x"]}})
    assert _owner_entity_completeness_gaps(
        {"entity": "item", "payload": {}}, discovery
    ) == ()


def test_apply_entity_defaults_noop_without_discovery():
    args = {"a": 1}
    assert _apply_entity_defaults_to_arguments(args, None) is args


def test_apply_entity_defaults_fills_payload_only():
    discovery = _discovery(
        {"item": {"defaults": {"ativo": True}, "required": ["ativo"]}}
    )
    out = _apply_entity_defaults_to_arguments(
        {"entity": "item", "payload": {"codigo": "1"}}, discovery
    )
    assert out == {
        "entity": "item",
        "payload": {"codigo": "1", "ativo": True},
    }


def test_argument_completeness_gaps_delegates_entity_schema():
    discovery = _discovery(
        {"item": {"required": ["codigo"], "properties": {}}}
    )
    gaps = _argument_completeness_gaps(
        {"entity": "item", "payload": {}}, None, discovery
    )
    assert gaps == ("codigo",)


def test_argument_completeness_gaps_non_mapping_empty():
    assert _argument_completeness_gaps(None, None, None) == ()


def test_required_gaps_output_bounded():
    schema = {
        "required": [f"f{i}" for i in range(40)],
        "properties": {},
    }
    gaps = _schema_required_gaps({}, schema)
    assert len(gaps) <= 8
    assert gaps[0] == "f0"
