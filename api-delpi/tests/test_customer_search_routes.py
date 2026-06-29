"""Smoke — GET /customers/search (critério de busca e contrato básico)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _body(response) -> dict:
    return response.json()


@pytest.fixture
def customer_client() -> TestClient:
    from app.interface.http.routes.customer_routes import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_search_customers_requires_criteria(customer_client: TestClient) -> None:
    response = customer_client.get("/customers/search")
    assert response.status_code == 400
    body = _body(response)
    assert body.get("success") is False
    assert "code" in (body.get("message") or "").lower()


@patch("app.interface.http.routes.customer_routes.build_search_customers_use_case")
def test_search_customers_accepts_name_only(
    mock_build: MagicMock,
    customer_client: TestClient,
) -> None:
    mock_use_case = MagicMock()
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [{"code": "000001", "store": "01", "name": "WEG EQUIPAMENTOS"}],
        "page": 1,
        "page_size": 20,
        "total": 1,
    }
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = customer_client.get("/customers/search", params={"name": "WEG"})
    assert response.status_code == 200
    body = _body(response)
    assert body.get("success") is True
    assert body.get("meta", {}).get("operationId") == "search_customers"
    assert len(body.get("data", {}).get("items", [])) == 1
