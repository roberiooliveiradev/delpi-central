import asyncio
import json
from unittest.mock import MagicMock, patch

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.main import http_exception_handler


def _body(response) -> dict:
    return json.loads(response.body.decode())


def test_http_exception_handler_returns_envelope_for_404() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/missing",
        "headers": [],
    }
    request = Request(scope)
    response = asyncio.run(
        http_exception_handler(request, StarletteHTTPException(404, "missing"))
    )
    body = _body(response)
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"


@patch("app.interface.http.routes.product_routes.build_search_products_use_case")
def test_product_detail_not_found_uses_envelope(mock_build_use_case) -> None:
    from app.interface.http.routes.product_routes import get_product_detail

    mock_use_case = MagicMock()
    mock_result = MagicMock()
    mock_result.items = []
    mock_use_case.execute.return_value = mock_result
    mock_build_use_case.return_value = mock_use_case

    response = get_product_detail("90269001")
    assert response.status_code == 404
    body = _body(response)
    assert body["error"]["code"] == "PRODUCT_NOT_FOUND"


@patch("app.interface.http.routes.product_routes.build_get_product_pricing")
def test_product_pricing_logical_failure_uses_envelope(mock_build_pricing) -> None:
    from app.interface.http.routes.product_routes import product_pricing

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "success": False,
        "message": "Product 90269001 not found",
    }
    mock_build_pricing.return_value = mock_use_case

    response = product_pricing("90269001")
    assert response.status_code == 404
    body = _body(response)
    assert body["error"]["code"] == "PRODUCT_PRICING_NOT_FOUND"
