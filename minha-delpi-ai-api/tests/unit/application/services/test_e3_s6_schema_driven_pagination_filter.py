"""E3.S6 — pagination/filter fast paths bound to OpenAPI schema."""

from __future__ import annotations

from app.application.services.schema_driven_pagination_filter_service import (
    SchemaDrivenPaginationFilterService,
)


def _stock_action(*, with_branch: bool = True, with_page: bool = True) -> dict:
    params = [
        {
            "name": "code",
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }
    ]
    if with_branch:
        params.append(
            {
                "name": "branch",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "enum": ["01", "02"]},
            }
        )
    if with_page:
        params.extend(
            [
                {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer"},
                },
                {
                    "name": "page_size",
                    "in": "query",
                    "schema": {"type": "integer"},
                },
            ]
        )
    return {
        "enabled": True,
        "method": "GET",
        "path": "/products/{code}/stock",
        "parametersSchema": params,
    }


def test_e3_s6_exact_phrases_page_and_size():
    plan = SchemaDrivenPaginationFilterService.plan(
        "página 3",
        action=_stock_action(),
        inherited_parameters={"code": "10080001", "page": 1, "page_size": 20},
        action_id="acme.products.stock",
    )
    assert plan is not None
    assert plan.ok is True
    assert plan.bind.parameters["page"] == 3
    assert plan.bind.parameters["code"] == "10080001"

    size = SchemaDrivenPaginationFilterService.plan(
        "traga 100 linhas",
        action=_stock_action(),
        inherited_parameters={"code": "10080001", "page": 1, "page_size": 20},
    )
    assert size is not None
    assert size.bind.parameters["page_size"] == 100


def test_e3_s6_next_page_and_branch_filter():
    nxt = SchemaDrivenPaginationFilterService.plan(
        "próxima página",
        action=_stock_action(),
        inherited_parameters={"code": "10080001", "page": 2},
    )
    assert nxt is not None
    assert nxt.bind.parameters["page"] == 3

    branch = SchemaDrivenPaginationFilterService.plan(
        "agora só filial 02",
        action=_stock_action(),
        inherited_parameters={"code": "10080001", "branch": "01"},
    )
    assert branch is not None
    assert branch.bind.parameters["branch"] == "02"
    assert any(item["argument"] == "branch" for item in branch.bind.conflicts)


def test_e3_s6_free_phrase_still_extracts_deterministic_values():
    plan = SchemaDrivenPaginationFilterService.plan(
        "pode me trazer a pagina 4 com 50 linhas por favor",
        action=_stock_action(),
        inherited_parameters={"code": "10080001", "page": 1},
    )
    assert plan is not None
    assert plan.bind.parameters["page"] == 4
    assert plan.bind.parameters["page_size"] == 50


def test_e3_s6_field_not_in_schema_is_stripped():
    plan = SchemaDrivenPaginationFilterService.plan(
        "agora só filial 02",
        action=_stock_action(with_branch=False),
        inherited_parameters={"code": "10080001"},
    )
    assert plan is not None
    assert "branch" in plan.refinement.argument_delta
    assert "branch" not in plan.bind.parameters
    # bind still ok because required code present; delta field dropped
    assert plan.bind.ok is True
    assert plan.ok is False


def test_e3_s6_warehouse_not_in_schema_stripped():
    plan = SchemaDrivenPaginationFilterService.plan(
        "filtre armazém 03",
        action=_stock_action(),
        inherited_parameters={"code": "10080001"},
    )
    assert plan is not None
    assert plan.refinement.argument_delta.get("warehouse") == "03"
    assert "warehouse" not in plan.bind.parameters


def test_e3_s6_no_signal_returns_none():
    assert (
        SchemaDrivenPaginationFilterService.plan(
            "olá, tudo bem?",
            action=_stock_action(),
            inherited_parameters={"code": "10080001"},
        )
        is None
    )
