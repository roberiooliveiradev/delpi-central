"""Tests for api-delpi Custom GPT Actions V1 (catalog + product search)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.application.gpt_actions.constants import (
    GPT_ACTIONS_OPERATION_IDS,
    GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
    GPT_SEARCH_RESPONSE_FIELDS,
)
from app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from app.application.gpt_actions.product_search_projection import (
    project_product_search_item,
    project_product_search_page,
)
from app.application.models.page import Page
from app.interface.http.routes.gpt_actions_routes import (
    gpt_get_catalog,
    gpt_get_openapi_schema,
    gpt_search_products,
)
from app.middleware.auth_middleware import _is_public_delpi_path


def test_openapi_schema_is_public_exact_path_only() -> None:
    assert _is_public_delpi_path("/gpt-actions/v1/openapi.json") is True
    assert _is_public_delpi_path("/apps/api-delpi/gpt-actions/v1/openapi.json") is True
    assert _is_public_delpi_path("/gpt-actions/v1/catalog") is False
    assert _is_public_delpi_path("/gpt-actions/v1/products/search") is False
    assert _is_public_delpi_path("/gpt-actions/v1/") is False


def test_openapi_builder_omits_openapi_path_and_uses_31() -> None:
    doc = build_gpt_actions_openapi(public_base_url="https://minhadelpi.com.br")
    assert doc["openapi"] in {"3.1.0", "3.1.1"}
    assert doc["servers"][0]["url"].startswith("https://")
    assert "/gpt-actions/v1/openapi.json" not in doc["paths"]
    assert set(doc["paths"].keys()) == {
        "/gpt-actions/v1/catalog",
        "/gpt-actions/v1/products/search",
    }
    ids = {
        doc["paths"][path]["get"]["operationId"] for path in doc["paths"]
    }
    assert ids == set(GPT_ACTIONS_OPERATION_IDS)


def test_project_product_search_item_allowlist_fail_closed() -> None:
    raw = {
        "code": "10080160",
        "description": "PARAFUSO",
        "group_code": "0101",
        "customer_reference": "SECRET-REF",
        "sale_price": 99.9,
        "standard_cost": 10.0,
        "ncm_ipi_position": "7318",
    }
    projected = project_product_search_item(raw)
    assert projected == {
        "product_code": "10080160",
        "description": "PARAFUSO",
        "group_category": "0101",
    }
    assert set(projected.keys()) == set(GPT_SEARCH_RESPONSE_FIELDS)
    assert "customer_reference" not in projected
    assert "sale_price" not in projected


def test_project_product_search_page_preserves_pagination() -> None:
    page = project_product_search_page(
        {
            "items": [{"code": "A", "description": "X", "group_code": "G1"}],
            "page": 2,
            "page_size": 50,
            "total": 51,
            "total_pages": 2,
        }
    )
    assert page["page"] == 2
    assert page["page_size"] == 50
    assert page["total"] == 51
    assert page["items"][0]["product_code"] == "A"


@patch("app.application.gpt_actions.dispatch_service.build_search_products_use_case")
def test_gpt_search_products_caps_page_size_and_projects(mock_build) -> None:
    product = MagicMock()
    product.to_dict.return_value = {
        "code": "10080160",
        "description": "PARAFUSO",
        "group_code": "0101",
        "customer_reference": "SHOULD-NOT-LEAK",
        "sale_price": 12.5,
    }
    mock_uc = MagicMock()
    mock_uc.execute.return_value = Page(
        items=[product],
        total=1,
        page=1,
        page_size=GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
    )
    mock_build.return_value = mock_uc

    response = gpt_search_products(
        code="1008",
        description=None,
        group_code=None,
        page=1,
        page_size=500,
    )
    body = json.loads(response.body.decode())

    assert body["success"] is True
    assert body["meta"]["operationId"] == "gpt_search_products"
    assert body["data"]["items"][0] == {
        "product_code": "10080160",
        "description": "PARAFUSO",
        "group_category": "0101",
    }
    assert "customer_reference" not in body["data"]["items"][0]
    request = mock_uc.execute.call_args[0][0]
    assert request.page_size == GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE
    assert request.customer_reference is None


@patch("app.application.gpt_actions.catalog_service.get_current_user")
def test_gpt_get_catalog_lists_v1_ops(mock_user) -> None:
    user = MagicMock()
    user.is_superadmin = True
    user.permissions = []
    mock_user.return_value = user

    response = gpt_get_catalog()
    body = json.loads(response.body.decode())

    assert body["success"] is True
    assert body["meta"]["operationId"] == "gpt_get_catalog"
    assert body["data"]["readOnly"] is True
    assert body["data"]["approvalReference"] == "API-DELPI-GPT-004A.2"
    assert "gpt_search_products" in body["data"]["allowedCapabilities"]
    assert body["data"]["dataClassification"] == "INTERNAL"


def test_gpt_get_openapi_schema_returns_document() -> None:
    response = gpt_get_openapi_schema()
    body = json.loads(response.body.decode())
    assert body["openapi"].startswith("3.1")
    assert "gpt_search_products" in json.dumps(body)
