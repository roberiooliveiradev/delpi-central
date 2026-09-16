"""Regression — consolidated branch scope (all ≡ omitted) across Category A/B/C/D."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.params import Depends as DependsParam
from fastapi.params import Query as QueryParam
from fastapi.testclient import TestClient

from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.dto.production_appointments.production_appointments_query_request import (
    ProductionAppointmentsQueryRequest,
)
from app.domain.totvs.protheus_branches import (
    normalize_branch_code,
    optional_concrete_branch,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    BRANCH_QUERY_REQUIRED,
    _normalize_optional_branch_scope,
)


def test_branch_query_optional_uses_depends_normalizer() -> None:
    dep = BRANCH_QUERY_OPTIONAL()
    assert isinstance(dep, DependsParam)
    assert dep.dependency is _normalize_optional_branch_scope
    assert optional_concrete_branch("all") is None
    assert optional_concrete_branch("01") == "01"


def test_category_a_playbook_all_equals_omitted() -> None:
    omitted = ProductPlaybookRequest(code="10080001", branch=None)
    all_scope = ProductPlaybookRequest(code="10080001", branch="all")
    assert omitted.branch is None
    assert all_scope.branch is None


def test_category_a_appointments_accepts_all_as_consolidated() -> None:
    req = ProductionAppointmentsQueryRequest.from_query(
        branch="all",
        require_branch=False,
    )
    assert req.branch is None


def test_category_c_concrete_branch_rejects_all() -> None:
    try:
        normalize_branch_code("all")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_category_c_branch_query_required_is_plain_query_not_all_normalizer() -> None:
    """Concrete 01|02 routes must not silently accept all via Depends normalizer."""
    param = BRANCH_QUERY_REQUIRED()
    assert isinstance(param, QueryParam)
    assert not isinstance(param, DependsParam)


def test_stock_balances_sql_all_has_no_filial_predicate() -> None:
    from app.infrastructure.persistence.totvs.supplies_repositories import (
        stock_balances_sql as sql,
    )

    where_all, params_all = sql.build_where_clause(
        branch="all", warehouse=None, only_positive=False
    )
    where_omit, params_omit = sql.build_where_clause(
        branch=None, warehouse=None, only_positive=False
    )
    assert where_all == where_omit
    assert params_all == params_omit == []
    assert "B2_FILIAL" not in where_all
    assert "all" not in params_all


def test_stock_http_branch_all_equals_omitted() -> None:
    from fastapi import FastAPI

    from app.interface.http.routes import product_routes as routes

    payloads: list[dict] = []

    class _UC:
        def execute(self, dto):
            payloads.append(
                {
                    "code": dto.code,
                    "branch": dto.branch,
                    "page": dto.page,
                    "page_size": dto.page_size,
                }
            )
            return {
                "items": [
                    {
                        "product_code": dto.code,
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 1,
                        "committed_quantity": 0,
                        "reserved_quantity": 0,
                        "available_quantity": 1,
                    }
                ],
                "total": 1,
                "page": dto.page,
                "page_size": dto.page_size,
            }

    app = FastAPI()
    app.include_router(routes.router, prefix="/products")
    client = TestClient(app)

    with patch.object(routes, "build_list_product_stock_use_case", return_value=_UC()):
        omitted = client.get("/products/10080001/stock")
        all_resp = client.get("/products/10080001/stock?branch=all")
        b01 = client.get("/products/10080001/stock?branch=01")
        b02 = client.get("/products/10080001/stock?branch=02")
        invalid = client.get("/products/10080001/stock?branch=03")

    assert omitted.status_code == 200, omitted.text
    assert all_resp.status_code == 200, all_resp.text
    assert b01.status_code == 200, b01.text
    assert b02.status_code == 200, b02.text
    assert invalid.status_code == 422

    assert payloads[0]["branch"] is None
    assert payloads[1]["branch"] is None
    assert payloads[2]["branch"] == "01"
    assert payloads[3]["branch"] == "02"
