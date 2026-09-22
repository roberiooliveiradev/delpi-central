"""Smoke — /production/shared-structure-intermediates."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.domain.services.production.shared_structure_intermediate_mapper import (
    SharedStructureIntermediateMapper,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def shared_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.shared_structure_intermediates_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_route() -> None:
    from app.interface.http.routes.production.shared_structure_intermediates_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/shared-structure-intermediates"
    assert "/production/shared-structure-intermediates" in paths


@patch(
    "app.interface.http.routes.production.shared_structure_intermediates_router"
    ".build_get_shared_structure_intermediates_use_case"
)
def test_returns_paged_list_envelope(mock_builder, shared_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "intermediate_code": "50320064",
                "intermediate_description": "PI A",
                "intermediate_type": "PI",
                "shared_pa_count": 2,
                "finished_products": [
                    {"product_code": "90262910", "description": "PA 1", "bom_level": 1},
                    {"product_code": "90262911", "description": "PA 2", "bom_level": 2},
                ],
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
        "filters": {"branch": "01", "movement_from": "2024-09-21"},
        "summary": {
            "checked_pa_count": 120,
            "shared_intermediate_count": 1,
            "max_shared_pa_count": 2,
        },
    }
    mock_builder.return_value = use_case

    response = shared_client.get(
        "/production/shared-structure-intermediates", params={"branch": "01"}
    )

    assert response.status_code == 200
    payload = _body(response)
    assert (
        payload["meta"]["operationId"]
        == "get_production_shared_structure_intermediates"
    )
    assert payload["meta"]["entity"] == "production_shared_structure_intermediates"
    assert payload["meta"]["shape"] == "paged_list"
    assert payload["data"]["items"][0]["intermediate_code"] == "50320064"


def test_mapper_groups_finished_products() -> None:
    rows = [
        {
            "component_code": "50320064",
            "component_description": "PI A",
            "component_type": "PI",
            "shared_pa_count": 2,
            "pa_code": "90262910",
            "pa_description": "PA 1",
            "bom_level": 1,
        },
        {
            "component_code": "50320064",
            "component_description": "PI A",
            "component_type": "PI",
            "shared_pa_count": 2,
            "pa_code": "90262911",
            "pa_description": "PA 2",
            "bom_level": 2,
        },
    ]
    items = SharedStructureIntermediateMapper.map_items(rows)
    assert len(items) == 1
    assert items[0]["shared_pa_count"] == 2
    assert len(items[0]["finished_products"]) == 2


def test_invalid_branch_returns_422(shared_client: TestClient) -> None:
    response = shared_client.get(
        "/production/shared-structure-intermediates", params={"branch": "99"}
    )
    assert response.status_code == 422
