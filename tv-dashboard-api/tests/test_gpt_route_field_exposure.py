"""Route-authoritative fields must reach the GPT/VISTA route DTO.

AUTHORITATIVE ROUTE FIELD > DERIVED TV CALCULATION: if the agent cannot see
which fields a route already returns, it generates redundant derivations
(addColumn/merge) instead of binding the authoritative field.
"""

from __future__ import annotations

from tv_app.application.gpt_actions.data_route_gpt_support import project_route_for_gpt


def test_route_projection_exposes_authoritative_value_fields():
    route = {
        "operationId": "get_commercial_rol_summary",
        "path": "/commercial/rol/summary",
        "httpMethod": "get",
        "label": "Resumo ROL",
        "paramSchema": {"properties": {"start_date": {"type": "string"}}},
        "valueFields": ["rol", "rol_target_pct"],
        "valueFieldLabels": {"rol": "ROL realizado", "rol_target_pct": "% do target"},
        "projectableFields": [
            {"name": "rol", "label": "ROL realizado", "semanticType": "currency"},
            {"name": "rol_target_pct", "label": "% do target", "semanticType": "percent"},
        ],
    }

    dto = project_route_for_gpt(route)

    assert dto["valueFields"] == ["rol", "rol_target_pct"]
    assert dto["valueFieldLabels"]["rol_target_pct"] == "% do target"
    assert [f["name"] for f in dto["projectableFields"]] == [
        "rol",
        "rol_target_pct",
    ]


def test_projectable_fields_projection_is_compact():
    """projectableFields full row may carry heavy keys — only identity keys."""
    route = {
        "operationId": "x",
        "projectableFields": [
            {
                "name": "a",
                "label": "A",
                "semanticType": "number",
                "internalNotes": "must not leak",
            }
        ],
    }
    dto = project_route_for_gpt(route)
    assert dto["projectableFields"] == [
        {"name": "a", "label": "A", "semanticType": "number"}
    ]


def test_route_projection_omits_absent_field_metadata():
    dto = project_route_for_gpt({"operationId": "x", "label": "X"})
    assert "valueFields" not in dto
    assert "projectableFields" not in dto
