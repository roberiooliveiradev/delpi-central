"""Smoke: GET /products/{code}/structure/excel — envelope document_export."""

from __future__ import annotations

import asyncio
import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from app.interface.http.routes.product_routes import structure_excel_public


def _request(*, headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/products/90261823/structure/excel",
        "raw_path": b"/products/90261823/structure/excel",
        "query_string": b"format=json",
        "headers": [
            (k.lower().encode(), v.encode())
            for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    return Request(scope)


@patch("app.interface.http.routes.product_routes.build_export_structure_excel_use_case")
def test_structure_excel_json_envelope_has_stable_contract(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = BytesIO(b"PK\x03\x04fake-xlsx")
    mock_build.return_value = use_case

    response = asyncio.run(
        structure_excel_public(
            _request(),
            code="90261823",
            format="json",
        )
    )
    body = json.loads(response.body.decode())

    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_product_structure_excel"
    assert body["meta"]["entity"] == "product_structure_excel"
    assert body["meta"]["shape"] == "document_export"
    assert body["data"]["downloadPath"] == (
        "/products/90261823/structure/excel?format=xlsx"
    )
    assert body["data"]["filename"] == "Estrutura_90261823.xlsx"
    assert body["data"]["download_url"] == body["data"]["downloadPath"]
    assert "downloadUrl" not in body["data"]


@patch("app.interface.http.routes.product_routes.build_export_structure_excel_use_case")
def test_structure_excel_json_adds_public_url_with_forwarded_host(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = BytesIO(b"PK\x03\x04fake-xlsx")
    mock_build.return_value = use_case

    response = asyncio.run(
        structure_excel_public(
            _request(
                headers={
                    "x-forwarded-host": "localhost",
                    "x-forwarded-proto": "http",
                }
            ),
            code="90261823",
            format="json",
        )
    )
    body = json.loads(response.body.decode())
    assert body["data"]["downloadUrl"] == (
        "http://localhost/apps/api-delpi/products/90261823/structure/excel?format=xlsx"
    )


def test_structure_excel_operation_id_registered() -> None:
    from app.interface.http.openapi_agent_metadata import PRODUCT_STRUCTURE_EXCEL
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    assert PRODUCT_STRUCTURE_EXCEL.get("operation_id") == "get_product_structure_excel"
    contract = ROUTE_CONTRACTS["get_product_structure_excel"]
    assert contract.entity == "product_structure_excel"
    assert contract.shape == "document_export"
