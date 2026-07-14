from tv_app.application.services.comunicado_input_filters_service import (
    collect_input_filter_contributions,
    intersect_param_schema_keys,
    is_value_allowed_by_param_schema,
    merge_filter_layers,
    resolve_input_param_schema_field,
)
from tv_app.application.services.public_filter_overrides_service import (
    allowlist_filter_overrides,
    collect_allowed_input_keys_from_playlist_slides,
    parse_filter_overrides_query,
)


SCHEMA_A = {
    "branch": {"type": "string", "enum": ["01", "02"], "label": "Filial"},
    "periodDays": {"type": "integer", "label": "Dias"},
}
SCHEMA_B = {
    "branch": {"type": "string", "enum": ["01", "02"], "label": "Filial"},
    "limit": {"type": "integer", "label": "Limite"},
}


def test_intersect_param_schema_keys():
    assert intersect_param_schema_keys([SCHEMA_A, SCHEMA_B]) == ["branch"]


def test_resolve_field_requires_intersection():
    assert resolve_input_param_schema_field("periodDays", [SCHEMA_A, SCHEMA_B]) is None
    field = resolve_input_param_schema_field("branch", [SCHEMA_A, SCHEMA_B])
    assert field and field.get("label") == "Filial"


def test_collect_slide_and_multi_source():
    blocks = [
        {
            "id": "i1",
            "type": "input",
            "style": {"zIndex": 1},
            "input": {"paramKey": "branch", "defaultValue": "01", "targetScope": "slide"},
        },
        {
            "id": "i2",
            "type": "input",
            "style": {"zIndex": 2},
            "input": {
                "paramKey": "periodDays",
                "defaultValue": 7,
                "targetScope": "sources",
                "targetSourceIds": ["src-a", "src-b"],
            },
        },
    ]
    contrib = collect_input_filter_contributions(blocks)
    assert contrib["slide"] == {"branch": "01"}
    assert contrib["bySourceId"]["src-a"] == {"periodDays": 7}
    assert contrib["bySourceId"]["src-b"] == {"periodDays": 7}


def test_zindex_wins_same_key():
    blocks = [
        {
            "id": "low",
            "type": "input",
            "style": {"zIndex": 1},
            "input": {"paramKey": "branch", "defaultValue": "01"},
        },
        {
            "id": "high",
            "type": "input",
            "style": {"zIndex": 5},
            "input": {"paramKey": "branch", "defaultValue": "02"},
        },
    ]
    assert collect_input_filter_contributions(blocks)["slide"]["branch"] == "02"


def test_schema_rejects_invalid_enum():
    blocks = [
        {
            "id": "i1",
            "type": "input",
            "input": {"paramKey": "branch", "defaultValue": "99"},
        }
    ]
    contrib = collect_input_filter_contributions(
        blocks,
        slide_schemas=[SCHEMA_A],
        schema_by_source_id={},
    )
    assert "branch" not in contrib["slide"]
    assert is_value_allowed_by_param_schema("01", SCHEMA_A["branch"]) is True


def test_merge_filter_layers():
    assert merge_filter_layers({"a": 1}, {"b": 2}, {"a": 3}) == {"a": 3, "b": 2}


def test_parse_and_allowlist_public_filters():
    parsed = parse_filter_overrides_query(
        '{"slide":{"branch":"01"},"bySourceId":{"src-a":{"periodDays":7}}}',
        {"limit": "10"},
    )
    assert parsed is not None
    assert parsed["slide"]["branch"] == "01"
    assert parsed["slide"]["limit"] == "10"
    assert parsed["bySourceId"]["src-a"]["periodDays"] == 7

    slides = [
        {
            "slideType": "native",
            "nativeScreenKey": "custom_message",
            "nativeConfig": {
                "blocks": [
                    {
                        "type": "input",
                        "input": {"paramKey": "branch", "targetScope": "slide"},
                    },
                    {
                        "type": "input",
                        "input": {
                            "paramKey": "periodDays",
                            "targetScope": "sources",
                            "targetSourceIds": ["src-a"],
                        },
                    },
                ]
            },
        }
    ]
    slide_keys, by_source = collect_allowed_input_keys_from_playlist_slides(slides)
    safe = allowlist_filter_overrides(
        parsed,
        allowed_slide_keys=slide_keys,
        allowed_by_source=by_source,
    )
    assert safe is not None
    assert safe["slide"] == {"branch": "01"}
    assert "limit" not in safe["slide"]
    assert safe["bySourceId"]["src-a"] == {"periodDays": 7}
