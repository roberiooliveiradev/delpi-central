"""Smoke e mapeamento — /production/production-order-sets."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.production.production_order_sets_request import (
    IncompleteOrderSetsRequest,
)
from app.domain.services.production.production_order_set_mapper import (
    ProductionOrderSetMapper,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def order_sets_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.production_order_sets_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_the_incomplete_route() -> None:
    from app.interface.http.routes.production.production_order_sets_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/production-order-sets"
    assert "/production/production-order-sets/incomplete" in paths


@patch(
    "app.interface.http.routes.production.production_order_sets_router"
    ".build_get_production_order_sets_incomplete_use_case"
)
def test_incomplete_returns_paged_list_envelope(
    mock_builder, order_sets_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "branch": "01",
                "set_number": "247192",
                "set_item": "01",
                "set_key": "24719201",
                "root_code": "90263364",
                "missing_count": 1,
                "extra_count": 0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
        "filters": {"branch": "01", "issued_from": None},
        "summary": {"checked_set_count": 491, "incomplete_set_count": 1},
    }
    mock_builder.return_value = use_case

    response = order_sets_client.get(
        "/production/production-order-sets/incomplete", params={"branch": "01"}
    )

    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_order_sets_incomplete"
    assert payload["meta"]["entity"] == "production_order_sets_incomplete"
    assert payload["meta"]["shape"] == "paged_list"
    assert payload["data"]["items"][0]["set_key"] == "24719201"


def test_invalid_branch_is_rejected_by_the_query_pattern(
    order_sets_client: TestClient,
) -> None:
    response = order_sets_client.get(
        "/production/production-order-sets/incomplete", params={"branch": "99"}
    )
    assert response.status_code == 422


@patch(
    "app.interface.http.routes.production.production_order_sets_router"
    ".build_get_production_order_sets_incomplete_use_case"
)
def test_invalid_issued_from_returns_400(
    mock_builder, order_sets_client: TestClient
) -> None:
    response = order_sets_client.get(
        "/production/production-order-sets/incomplete",
        params={"issued_from": "ontem"},
    )
    assert response.status_code == 400


def test_request_maps_all_scope_to_consolidated_branch() -> None:
    request = IncompleteOrderSetsRequest.from_params(branch="all", page=3, page_size=20)

    assert request.branch is None
    assert request.offset == 40
    assert request.filter_kwargs() == {"branch": None, "issued_from": None}
    assert request.filters_dict()["branch"] == "all"


def test_request_converts_issued_from_to_protheus_date() -> None:
    request = IncompleteOrderSetsRequest.from_params(issued_from="2025-01-01")

    assert request.filter_kwargs()["issued_from"] == "20250101"
    assert request.filters_dict()["issued_from"] == "2025-01-01"


def test_mapper_groups_diff_rows_into_one_item_per_set() -> None:
    rows = [
        {
            "branch": "01",
            "set_number": "247192",
            "set_item": "01",
            "root_code": "90263364",
            "root_description": "CABO DE LIGACAO",
            "root_type": "PA",
            "root_order_key": "24719201001",
            "due_date": "2026-08-24",
            "reference_date": "20260812",
            "order_count": 2,
            "open_order_count": 2,
            "expected_component_count": 2,
            "created_component_count": 1,
            "missing_count": 1,
            "extra_count": 1,
            "component_code": "50090002",
            "component_description": "SEPARADOR DE CABOS",
            "component_type": "PI",
            "bom_level": 2,
            "component_order_key": "",
            "is_missing": 1,
            "is_extra": 0,
        },
        {
            "branch": "01",
            "set_number": "247192",
            "set_item": "01",
            "root_code": "90263364",
            "root_description": "CABO DE LIGACAO",
            "root_type": "PA",
            "root_order_key": "24719201001",
            "due_date": "2026-08-24",
            "reference_date": "20260812",
            "order_count": 2,
            "open_order_count": 2,
            "expected_component_count": 2,
            "created_component_count": 1,
            "missing_count": 1,
            "extra_count": 1,
            "component_code": "50319902",
            "component_description": "CHICOTE INTERNO",
            "component_type": "PI",
            "bom_level": 0,
            "component_order_key": "24719201004",
            "is_missing": 0,
            "is_extra": 1,
        },
    ]

    items = ProductionOrderSetMapper.map_sets(rows)

    assert len(items) == 1
    item = items[0]
    assert item["set_key"] == "24719201"
    assert item["issued_at"] == "2026-08-12"
    assert item["missing_components"] == [
        {
            "product_code": "50090002",
            "description": "SEPARADOR DE CABOS",
            "product_type": "PI",
            "bom_level": 2,
        }
    ]
    assert item["extra_components"] == [
        {
            "product_code": "50319902",
            "description": "CHICOTE INTERNO",
            "product_type": "PI",
            "production_order": "24719201004",
        }
    ]


def test_mapper_keeps_sets_apart_by_item_within_the_same_number() -> None:
    rows = [
        {
            "branch": "01",
            "set_number": "100000",
            "set_item": "01",
            "component_code": "50000001",
            "is_missing": 1,
            "is_extra": 0,
        },
        {
            "branch": "01",
            "set_number": "100000",
            "set_item": "02",
            "component_code": "50000002",
            "is_missing": 1,
            "is_extra": 0,
        },
    ]

    items = ProductionOrderSetMapper.map_sets(rows)

    assert [item["set_key"] for item in items] == ["10000001", "10000002"]
