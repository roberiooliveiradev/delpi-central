"""E3.S4 — schema-driven argument binder (OpenAPI authority)."""

from __future__ import annotations

from app.application.services.schema_driven_argument_binder_service import (
    SchemaDrivenArgumentBinderService,
)
from app.domain.entities.turn_refinement import TurnRefinement


def _stock_action() -> dict:
    return {
        "enabled": True,
        "method": "GET",
        "path": "/products/{code}/stock",
        "parametersSchema": [
            {
                "name": "code",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "branch",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "enum": ["01", "02"]},
            },
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
            },
            {
                "name": "page_size",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
            },
            {
                "name": "start_date",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "format": "date"},
            },
        ],
    }


def _post_action() -> dict:
    return {
        "enabled": True,
        "method": "POST",
        "path": "/notes",
        "parametersSchema": [],
        "requestBodySchema": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["title"],
                        "additionalProperties": False,
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    }
                }
            },
        },
    }


def test_e3_s4_required_present_and_missing():
    action = _stock_action()
    ok = SchemaDrivenArgumentBinderService.bind(
        action=action,
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"page": 2},
        },
        inherited_parameters={"code": "10080001", "page": 1},
    )
    assert ok.ok is True
    assert ok.parameters["code"] == "10080001"
    assert ok.parameters["page"] == 2

    missing = SchemaDrivenArgumentBinderService.bind(
        action=action,
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"page": 2},
        },
        inherited_parameters={},
    )
    assert missing.ok is False
    assert "code" in missing.missing or "missing_required_parameter" in missing.errors
    assert missing.clarification_reason


def test_e3_s4_path_query_and_unknown_stripped():
    result = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {
                "page": 3,
                "routeSegment": "stock",
                "warehouse": "01",
            },
        },
        inherited_parameters={"code": "10080001", "branch": "01"},
    )
    assert result.ok is True
    assert result.parameters == {"code": "10080001", "branch": "01", "page": 3}
    assert "warehouse" not in result.parameters
    assert "routeSegment" not in result.parameters


def test_e3_s4_invalid_enum_and_type():
    bad_enum = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"branch": "99"},
        },
        inherited_parameters={"code": "10080001"},
    )
    assert bad_enum.ok is False
    assert "invalid_enum" in bad_enum.errors

    bad_type = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"page": "abc"},
        },
        inherited_parameters={"code": "10080001"},
    )
    assert bad_type.ok is False
    assert "invalid_type" in bad_type.errors


def test_e3_s4_date_format_coercion_and_invalid_format():
    coerced = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"start_date": "2026-09-10"},
        },
        inherited_parameters={"code": "10080001"},
        message="em 10/09/2026",
    )
    assert coerced.ok is True
    assert coerced.parameters["start_date"] == "2026-09-10"

    invalid = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"start_date": "not-a-date"},
        },
        inherited_parameters={"code": "10080001"},
    )
    assert invalid.ok is False
    assert "invalid_format" in invalid.errors


def test_e3_s4_body_required_and_additional_properties_false():
    ok = SchemaDrivenArgumentBinderService.bind(
        action=_post_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"body": {"title": "Ata", "body": "texto"}},
        },
    )
    assert ok.ok is True
    assert ok.body == {"title": "Ata", "body": "texto"}

    missing_title = SchemaDrivenArgumentBinderService.bind(
        action=_post_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"body": {"body": "sem título"}},
        },
    )
    assert missing_title.ok is False
    assert "title" in missing_title.missing or missing_title.clarification_reason

    extra = SchemaDrivenArgumentBinderService.bind(
        action=_post_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.9,
            "argumentDelta": {"body": {"title": "X", "secret": "nope"}},
        },
    )
    assert extra.ok is False
    assert "unknown_parameter" in extra.errors


def test_e3_s4_conflicting_inherited_explicit_wins():
    result = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement=TurnRefinement.from_dict(
            {
                "kind": "argument_delta",
                "confidence": 0.9,
                "argumentDelta": {"branch": "02", "page": "2"},
            }
        ),
        inherited_parameters={"code": "10080001", "branch": "01", "page": 1},
    )
    assert result.ok is True
    assert result.parameters["branch"] == "02"
    assert result.parameters["page"] == 2
    assert any(item["argument"] == "branch" for item in result.conflicts)


def test_e3_s4_does_not_invent_missing_required():
    result = SchemaDrivenArgumentBinderService.bind(
        action=_stock_action(),
        refinement={
            "kind": "argument_delta",
            "confidence": 0.5,
            "argumentDelta": {},
        },
        inherited_parameters={"page": 1},
        message="próxima página",
    )
    assert result.ok is False
    assert result.parameters.get("code") is None
