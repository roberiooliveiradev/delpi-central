from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.materials_service import (
    MaterialsService,
    _MaterialsSnapshotCache,
)
from production_control_app.domain.errors import BranchAccessDenied
from production_control_app.domain.services.materials_excess import (
    classify_fully_eliminable,
    classify_shortage_products,
)

FULL_PERMS = (
    "production-control.access",
    "production-control.materials.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _user(*permissions: str, superadmin: bool = False):
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


def _item(**overrides: Any) -> dict[str, Any]:
    row = {
        "branch": "01",
        "request_number": "SC001",
        "request_item": "01",
        "product_code": "10020113",
        "product_description": "Cobre",
        "warehouse": "01",
        "unit": "KG",
        "open_quantity": 50.0,
        "open_quantity_primary_unit": 50.0,
        "required_date": "2026-08-20",
        "issue_date": "2026-08-01",
        "supplier_name": "Fornecedor",
        "product_coverage": {
            "available_stock": 80.0,
            "safety_stock": 0.0,
            "open_purchase_order_quantity": 20.0,
            "open_commitment_quantity": 10.0,
            "projected_balance": 90.0,
            "primary_unit": "KG",
        },
    }
    coverage = overrides.pop("product_coverage", None)
    row.update(overrides)
    if coverage is not None:
        row["product_coverage"] = coverage
    return row


def _product(**overrides: Any) -> dict[str, Any]:
    row = {
        "product_code": "10020113",
        "product_description": "Cobre",
        "unit": "KG",
        "product_coverage": {
            "available_stock": 80.0,
            "safety_stock": 0.0,
            "open_purchase_order_quantity": 20.0,
            "open_commitment_quantity": 10.0,
            "projected_balance": 90.0,
            "primary_unit": "KG",
        },
    }
    coverage = overrides.pop("product_coverage", None)
    row.update(overrides)
    if coverage is not None:
        row["product_coverage"] = coverage
    return row


def test_classify_all_requests_when_projected_covers_safety_stock() -> None:
    rows = classify_fully_eliminable(
        [
            _item(request_number="SC001", request_item="01", open_quantity_primary_unit=50),
            _item(request_number="SC002", request_item="01", open_quantity_primary_unit=10),
        ]
    )
    assert [row.id for row in rows] == ["SC001/01", "SC002/01"]
    assert rows[0].needed_from_sc1 == 0
    assert rows[0].projected_balance == 90.0


def test_classify_keeps_oldest_request_to_cover_safety_stock() -> None:
    coverage = {
        "available_stock": 80.0,
        "safety_stock": 100.0,
        "open_purchase_order_quantity": 20.0,
        "open_commitment_quantity": 10.0,
        "projected_balance": 90.0,
        "primary_unit": "KG",
    }
    rows = classify_fully_eliminable(
        [
            _item(
                request_number="SC010",
                request_item="01",
                open_quantity_primary_unit=1000.0,
                product_coverage=coverage,
            ),
            _item(
                request_number="SC011",
                request_item="01",
                open_quantity_primary_unit=30.0,
                product_coverage=coverage,
            ),
        ]
    )
    assert [row.id for row in rows] == ["SC011/01"]
    assert rows[0].needed_from_sc1 == 10.0
    assert rows[0].safety_stock == 100.0


def test_classify_keeps_oldest_request_when_only_partially_needed() -> None:
    coverage = {
        "available_stock": 0.0,
        "safety_stock": 0.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 10.0,
        "projected_balance": -10.0,
        "primary_unit": "KG",
    }
    rows = classify_fully_eliminable(
        [
            _item(
                request_number="SC010",
                request_item="01",
                open_quantity_primary_unit=1000.0,
                product_coverage=coverage,
            ),
            _item(
                request_number="SC011",
                request_item="01",
                open_quantity_primary_unit=30.0,
                product_coverage=coverage,
            ),
        ]
    )
    assert [row.id for row in rows] == ["SC011/01"]
    assert rows[0].needed_from_sc1 == 10.0


def test_classify_skips_product_without_fully_unused_request() -> None:
    coverage = {
        "available_stock": 0.0,
        "safety_stock": 0.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 100.0,
        "projected_balance": -100.0,
        "primary_unit": "KG",
    }
    rows = classify_fully_eliminable(
        [
            _item(
                request_number="SC020",
                request_item="01",
                open_quantity_primary_unit=40.0,
                product_coverage=coverage,
            ),
            _item(
                request_number="SC021",
                request_item="01",
                open_quantity_primary_unit=40.0,
                product_coverage=coverage,
            ),
            _item(
                request_number="SC022",
                request_item="01",
                open_quantity_primary_unit=50.0,
                product_coverage=coverage,
            ),
        ]
    )
    assert rows == []


def test_classify_shortage_when_sc1_does_not_reach_safety_stock() -> None:
    coverage = {
        "available_stock": 10.0,
        "safety_stock": 100.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 0.0,
        "projected_balance": 10.0,
        "primary_unit": "KG",
    }
    rows = classify_shortage_products(
        [_item(open_quantity_primary_unit=20.0, product_coverage=coverage)],
        [_product(product_coverage=coverage)],
    )
    assert len(rows) == 1
    assert rows[0].needed_from_sc1 == 90.0
    assert rows[0].open_sc1_quantity == 20.0
    assert rows[0].shortage_quantity == 70.0


def test_classify_shortage_includes_product_without_any_request() -> None:
    coverage = {
        "available_stock": 5.0,
        "safety_stock": 40.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 0.0,
        "projected_balance": 5.0,
        "primary_unit": "KG",
    }
    rows = classify_shortage_products([], [_product(product_coverage=coverage)])
    assert len(rows) == 1
    assert rows[0].open_sc1_quantity == 0.0
    assert rows[0].shortage_quantity == 35.0


def test_classify_shortage_skips_when_sc1_covers_safety_stock() -> None:
    coverage = {
        "available_stock": 90.0,
        "safety_stock": 100.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 0.0,
        "projected_balance": 90.0,
        "primary_unit": "KG",
    }
    rows = classify_shortage_products(
        [_item(open_quantity_primary_unit=20.0, product_coverage=coverage)],
        [_product(product_coverage=coverage)],
    )
    assert rows == []


class FakeMaterialsGateway:
    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        products: list[dict[str, Any]] | None = None,
    ) -> None:
        self.items = items if items is not None else [_item()]
        self.products = products if products is not None else [_product()]
        self.calls = 0

    def fetch_purchase_request_open_coverage(self, *, branch: str) -> dict[str, Any]:
        self.calls += 1
        assert branch == "01"
        return {"data": {"items": self.items, "products": self.products}}


def test_materials_service_pages_and_summarizes() -> None:
    service = MaterialsService(
        FakeMaterialsGateway(
            [
                _item(request_number="SC001", product_code="10020113"),
                _item(request_number="SC002", product_code="20000001"),
            ],
            [
                _product(product_code="10020113"),
                _product(product_code="20000001", product_description="Aço"),
            ],
        ),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    payload = service.list_materials(
        _user(*FULL_PERMS),
        branch="01",
        page=1,
        page_size=1,
    )
    assert payload["view"] == "excess"
    assert payload["pagination"]["total"] == 2
    assert payload["pagination"]["page_size"] == 1
    assert len(payload["items"]) == 1
    assert payload["summary"]["excess_product_count"] == 2
    assert payload["issues"][0]["id"] == "excess"
    assert payload["issues"][0]["product_count"] == 2
    assert "unit_price" not in payload["items"][0]


def test_materials_service_search_filters_product() -> None:
    service = MaterialsService(
        FakeMaterialsGateway(
            [
                _item(request_number="SC001", product_code="10020113"),
                _item(request_number="SC002", product_code="20000001"),
            ],
            [
                _product(product_code="10020113"),
                _product(product_code="20000001"),
            ],
        ),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    payload = service.list_materials(
        _user(*FULL_PERMS),
        branch="01",
        search="2000",
    )
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["product_code"] == "20000001"


def test_materials_service_lists_shortage_view() -> None:
    coverage = {
        "available_stock": 5.0,
        "safety_stock": 40.0,
        "open_purchase_order_quantity": 0.0,
        "open_commitment_quantity": 0.0,
        "projected_balance": 5.0,
        "primary_unit": "KG",
    }
    service = MaterialsService(
        FakeMaterialsGateway(
            items=[],
            products=[_product(product_coverage=coverage)],
        ),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    payload = service.list_materials(
        _user(*FULL_PERMS),
        branch="01",
        view="shortage",
    )
    assert payload["view"] == "shortage"
    assert payload["items"][0]["kind"] == "shortage"
    assert payload["items"][0]["shortage_quantity"] == 35.0
    assert payload["summary"]["shortage_product_count"] == 1
    assert payload["issues"][1]["product_count"] == 1


def test_materials_service_denies_without_permission() -> None:
    service = MaterialsService(
        FakeMaterialsGateway(),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    with pytest.raises(PermissionError):
        service.list_materials(
            _user(
                "production-control.access",
                "production-control.view.filial-01",
            ),
            branch="01",
        )


def test_materials_service_denies_other_branch() -> None:
    service = MaterialsService(
        FakeMaterialsGateway(),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    with pytest.raises(BranchAccessDenied):
        service.list_materials(
            _user(
                "production-control.access",
                "production-control.materials.view",
                "production-control.view.filial-01",
            ),
            branch="02",
        )


def test_materials_route_returns_envelope() -> None:
    from production_control_app.interface.http.routes import materials_routes

    original = materials_routes.build_materials_service
    service = MaterialsService(
        FakeMaterialsGateway(),
        cache=_MaterialsSnapshotCache(ttl_seconds=120),
    )
    materials_routes.build_materials_service = lambda: service  # type: ignore[assignment]
    try:
        app = FastAPI()

        @app.middleware("http")
        async def inject_user(request, call_next):
            request.state.user = _user(*FULL_PERMS)
            return await call_next(request)

        app.include_router(materials_routes.router)
        client = TestClient(app)
        response = client.get("/materials", params={"branch": "01"})
    finally:
        materials_routes.build_materials_service = original  # type: ignore[assignment]

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"][0]["request_number"] == "SC001"
    assert body["data"]["issues"][0]["title"] == "Excesso de solicitações"
