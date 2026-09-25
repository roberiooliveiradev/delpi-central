"""SQL e smoke — bloqueio de inventário SB2.B2_DTINV/B2_DINVFIM em lote."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.product.list_product_inventory_blocks_request import (
    ListProductInventoryBlocksRequest,
)
from app.application.use_cases.product.list_product_inventory_blocks_use_case import (
    ListProductInventoryBlocksUseCase,
)
from app.domain.totvs.protheus_inventory_block import is_inventory_blocked
from app.domain.totvs.protheus_product_codes import MAX_PRODUCT_CODES
from app.infrastructure.persistence.totvs.product_repositories.product_inventory_blocks_sql import (
    inventory_blocks_sql,
)
from app.infrastructure.persistence.totvs.product_repositories.product_stock_repository import (
    ProductStockRepository,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def blocks_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.product_routes import router

    app = FastAPI()
    app.include_router(router, prefix="/products")
    return TestClient(app)


def test_inventory_blocks_sql_filters_branch_warehouse_and_codes() -> None:
    src = inventory_blocks_sql(product_count=2)
    assert "SB2010" in src
    assert "B2_DTINV" in src
    assert "B2_DINVFIM" in src
    assert "B2_FILIAL" in src
    assert "B2_LOCAL" in src
    assert "B2_COD" in src
    assert "D_E_L_E_T_ = ''" in src
    assert "IN (?, ?)" in src
    assert src.count("?") == 4  # filial + armazém + 2 códigos


def test_inventory_blocks_sql_rejects_empty_count() -> None:
    with pytest.raises(ValueError):
        inventory_blocks_sql(product_count=0)


@pytest.mark.parametrize(
    ("start", "end", "as_of", "expected"),
    [
        (None, None, date(2026, 9, 25), False),
        ("", "20260930", date(2026, 9, 25), False),
        ("20260920", None, date(2026, 9, 25), True),
        ("20260920", "", date(2026, 9, 25), True),
        ("20260920", "20260930", date(2026, 9, 25), True),
        ("20260920", "20260922", date(2026, 9, 25), False),
        ("20260926", "20260930", date(2026, 9, 25), False),
        ("2026-09-20", "2026-09-30", date(2026, 9, 25), True),
    ],
)
def test_is_inventory_blocked_window(start, end, as_of, expected) -> None:
    assert is_inventory_blocked(block_start=start, block_end=end, as_of=as_of) is expected


def test_repository_batch_passes_branch_warehouse_then_codes() -> None:
    repo = ProductStockRepository()
    with patch.object(
        ProductStockRepository, "execute_query", return_value=[]
    ) as execute, patch.object(
        ProductStockRepository, "__enter__", return_value=repo
    ), patch.object(
        ProductStockRepository, "__exit__", return_value=False
    ):
        assert (
            repo.fetch_inventory_blocks(
                branch="01", warehouse="01", product_codes=[]
            )
            == []
        )
        execute.assert_not_called()

        repo.fetch_inventory_blocks(
            branch="01",
            warehouse="01",
            product_codes=["10070821", "10070822"],
        )
        assert execute.call_args.args[1] == ("01", "01", "10070821", "10070822")


def test_use_case_maps_blocked_flag() -> None:
    repository = MagicMock()
    repository.fetch_inventory_blocks.return_value = [
        {
            "product_code": "10070821",
            "branch": "01",
            "warehouse": "01",
            "inventory_block_start": "20260901",
            "inventory_block_end": "",
        },
        {
            "product_code": "10070822",
            "branch": "01",
            "warehouse": "01",
            "inventory_block_start": "",
            "inventory_block_end": "",
        },
    ]
    result = ListProductInventoryBlocksUseCase(repository).execute(
        ListProductInventoryBlocksRequest(
            branch="01",
            warehouse="01",
            product_codes=["10070821", "10070822"],
        ),
        as_of=date(2026, 9, 25),
    )
    by_code = {item["product_code"]: item for item in result["items"]}
    assert by_code["10070821"]["inventory_blocked"] is True
    assert by_code["10070821"]["inventory_block_start"] == "20260901"
    assert by_code["10070821"]["inventory_block_start_iso"] == "2026-09-01"
    assert by_code["10070822"]["inventory_blocked"] is False
    assert result["summary"]["blocked_count"] == 1


def test_use_case_without_codes_does_not_touch_repository() -> None:
    repository = MagicMock()
    result = ListProductInventoryBlocksUseCase(repository).execute(
        ListProductInventoryBlocksRequest(branch="01", product_codes=[])
    )
    repository.fetch_inventory_blocks.assert_not_called()
    assert result["items"] == []


def test_batch_route_returns_envelope(blocks_client: TestClient) -> None:
    with patch(
        "app.interface.http.routes.product_routes.build_list_product_inventory_blocks_use_case"
    ) as build:
        use_case = MagicMock()
        use_case.execute.return_value = {
            "branch": "01",
            "warehouse": "01",
            "as_of": "2026-09-25",
            "product_codes": ["10070821"],
            "items": [
                {
                    "product_code": "10070821",
                    "branch": "01",
                    "warehouse": "01",
                    "inventory_block_start": "20260901",
                    "inventory_block_end": None,
                    "inventory_block_start_iso": "2026-09-01",
                    "inventory_block_end_iso": None,
                    "inventory_blocked": True,
                },
            ],
            "summary": {
                "requested_count": 1,
                "returned_count": 1,
                "blocked_count": 1,
            },
        }
        build.return_value = use_case
        response = blocks_client.post(
            "/products/inventory-blocks",
            json={"branch": "01", "product_codes": ["10070821"], "warehouse": "01"},
        )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["data"]["items"][0]["inventory_blocked"] is True
    assert payload["meta"]["operationId"] == "list_product_inventory_blocks"


def test_batch_route_rejects_invalid_branch(blocks_client: TestClient) -> None:
    response = blocks_client.post(
        "/products/inventory-blocks",
        json={"branch": "99", "product_codes": ["10070821"]},
    )
    assert response.status_code == 400


def test_batch_route_rejects_over_cap(blocks_client: TestClient) -> None:
    response = blocks_client.post(
        "/products/inventory-blocks",
        json={
            "branch": "01",
            "product_codes": [f"P{i:04d}" for i in range(MAX_PRODUCT_CODES + 1)],
        },
    )
    assert response.status_code == 400
