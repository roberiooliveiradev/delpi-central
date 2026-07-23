import json
from unittest.mock import MagicMock, patch

from app.interface.http.routes.product_routes import stock


@patch("app.interface.http.routes.product_routes.build_list_product_stock_use_case")
def test_product_stock_returns_meta_shape(mock_build_stock) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
    }
    mock_build_stock.return_value = mock_use_case

    response = stock("90269001")
    body = json.loads(response.body.decode())
    assert body["meta"]["shape"] == "paged_list"
    assert body["meta"]["entity"] == "product_stock"
    assert body["meta"]["operationId"] == "get_product_stock"
    assert body["meta"]["dataVersion"] == "2026-07"
