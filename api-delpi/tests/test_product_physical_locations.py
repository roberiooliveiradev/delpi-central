"""SQL e smoke — locais físicos SBZ010.BZ_MPLOCAL em lote."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.product.list_product_physical_locations_request import (
    ListProductPhysicalLocationsRequest,
)
from app.application.use_cases.product.list_product_physical_locations_use_case import (
    ListProductPhysicalLocationsUseCase,
)
from app.domain.totvs.protheus_product_codes import MAX_PRODUCT_CODES, require_product_codes
from app.infrastructure.persistence.totvs.product_repositories.product_physical_locations_sql import (
    physical_locations_sql,
)
from app.infrastructure.persistence.totvs.product_repositories.product_stock_repository import (
    ProductStockRepository,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def locations_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.product_routes import router

    app = FastAPI()
    app.include_router(router, prefix="/products")
    return TestClient(app)


def test_physical_locations_sql_filters_branch_and_codes() -> None:
    src = physical_locations_sql(product_count=2)
    assert "SBZ010" in src
    assert "BZ_MPLOCAL" in src
    assert "BZ_FILIAL" in src
    assert "BZ_COD" in src
    assert "D_E_L_E_T_ = ''" in src
    assert "IN (?, ?)" in src
    assert src.count("?") == 3  # filial + 2 códigos


def test_physical_locations_sql_rejects_empty_count() -> None:
    with pytest.raises(ValueError):
        physical_locations_sql(product_count=0)


def test_require_product_codes_dedupes_and_caps() -> None:
    assert require_product_codes([" 10070821 ", "10070821", "10070822"]) == (
        "10070821",
        "10070822",
    )
    assert require_product_codes([]) == ()
    with pytest.raises(ValueError, match="excede"):
        require_product_codes([f"P{i:04d}" for i in range(MAX_PRODUCT_CODES + 1)])


def test_repository_batch_passes_branch_then_codes_and_skips_empty() -> None:
    repo = ProductStockRepository()
    with patch.object(
        ProductStockRepository, "execute_query", return_value=[]
    ) as execute, patch.object(
        ProductStockRepository, "__enter__", return_value=repo
    ), patch.object(
        ProductStockRepository, "__exit__", return_value=False
    ):
        assert repo.fetch_physical_locations(branch="01", product_codes=[]) == []
        execute.assert_not_called()

        repo.fetch_physical_locations(
            branch="01", product_codes=["10070821", "10070822"]
        )
        assert execute.call_args.args[1] == ("01", "10070821", "10070822")


def test_use_case_maps_items_and_skips_empty_codes() -> None:
    repository = MagicMock()
    repository.fetch_physical_locations.return_value = [
        {"product_code": "10070821", "physical_location": " A-01 "},
        {"product_code": "", "physical_location": "X"},
    ]
    result = ListProductPhysicalLocationsUseCase(repository).execute(
        ListProductPhysicalLocationsRequest(
            branch="01",
            product_codes=["10070821", "10070822"],
        )
    )
    assert result["items"] == [
        {"product_code": "10070821", "physical_location": "A-01"},
    ]
    assert result["summary"]["requested_count"] == 2
    assert result["summary"]["returned_count"] == 1


def test_use_case_without_codes_does_not_touch_repository() -> None:
    repository = MagicMock()
    result = ListProductPhysicalLocationsUseCase(repository).execute(
        ListProductPhysicalLocationsRequest(branch="01", product_codes=[])
    )
    repository.fetch_physical_locations.assert_not_called()
    assert result["items"] == []


def test_batch_route_returns_envelope(locations_client: TestClient) -> None:
    with patch(
        "app.interface.http.routes.product_routes.build_list_product_physical_locations_use_case"
    ) as build:
        use_case = MagicMock()
        use_case.execute.return_value = {
            "branch": "01",
            "product_codes": ["10070821"],
            "items": [
                {"product_code": "10070821", "physical_location": "A-01"},
            ],
            "summary": {"requested_count": 1, "returned_count": 1},
        }
        build.return_value = use_case
        response = locations_client.post(
            "/products/physical-locations",
            json={"branch": "01", "product_codes": ["10070821"]},
        )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["data"]["items"][0]["physical_location"] == "A-01"
    assert payload["meta"]["operationId"] == "list_product_physical_locations"


def test_batch_route_rejects_invalid_branch(locations_client: TestClient) -> None:
    response = locations_client.post(
        "/products/physical-locations",
        json={"branch": "99", "product_codes": ["10070821"]},
    )
    assert response.status_code == 400


def test_batch_route_rejects_over_cap(locations_client: TestClient) -> None:
    response = locations_client.post(
        "/products/physical-locations",
        json={
            "branch": "01",
            "product_codes": [f"P{i:04d}" for i in range(MAX_PRODUCT_CODES + 1)],
        },
    )
    assert response.status_code == 400
