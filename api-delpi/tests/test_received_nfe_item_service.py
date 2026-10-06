"""Orquestração do detalhe da NF-e com tradução SA5/SB1."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.services.lancamento_notas_fiscais.received_nfe_item_service import (
    ReceivedNfeItemService,
)
from app.core.exceptions import DatabaseConnectionError
from app.domain.services.lancamento_notas_fiscais.exceptions import InvoicePostingErpQueryError
from app.infrastructure.gateways.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGateway,
    FinancialReceivedInvoiceGatewayError,
)

DOCUMENT_ID = "aabbccddeeff001122334455"
ENTITY_ID = "c" * 24
ACCESS_KEY = "1" * 20 + "55" + "2" * 22
CNPJ = "12345678000199"


def _detail() -> dict:
    return {
        "documentType": "nfe",
        "documentId": DOCUMENT_ID,
        "providerEntityId": ENTITY_ID,
        "branchCode": "01",
        "accessKey": ACCESS_KEY,
        "number": "000000123",
        "series": "001",
        "issuer": {"name": "FORNECEDOR", "cnpj": CNPJ},
        "items": [
            {
                "itemNumber": "1",
                "supplierProductCode": "00001234",
                "supplierProductDescription": "PARAFUSO",
                "quantity": "10",
                "unit": "PC",
            },
            {
                "itemNumber": "2",
                "supplierProductCode": "00001234",
                "supplierProductDescription": "PARAFUSO",
                "quantity": "1",
                "unit": "PC",
            },
            {
                "itemNumber": "3",
                "supplierProductCode": "SEM-AMARRACAO",
                "supplierProductDescription": "NADA",
                "quantity": "2",
                "unit": "UN",
            },
        ],
    }


def _service(rows: list[dict] | None = None, *, supplier_cnpj: str = CNPJ, gateway_error: Exception | None = None):
    calls: list[dict] = []

    class Gateway:
        def get_nfe_detail(self, **kwargs):
            if gateway_error:
                raise gateway_error
            calls.append(kwargs)
            return _detail()

    class Suppliers:
        def get_supplier(self, *, supplier_code: str, supplier_store: str):
            if supplier_cnpj == "missing":
                return None
            return {
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "tax_id": supplier_cnpj,
            }

    class Mappings:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def list_mappings(self, **kwargs):
            self.calls.append(kwargs)
            if rows is None:
                raise DatabaseConnectionError("falha")
            return rows

    mappings = Mappings()
    service = ReceivedNfeItemService(
        gateway=Gateway(),  # type: ignore[arg-type]
        suppliers=Suppliers(),  # type: ignore[arg-type]
        mappings=mappings,  # type: ignore[arg-type]
    )
    return service, mappings, calls


def _execute(service: ReceivedNfeItemService, **overrides):
    payload = {
        "authorization": "Bearer user-jwt",
        "document_id": DOCUMENT_ID,
        "provider_entity_id": ENTITY_ID,
        "access_key": ACCESS_KEY,
        "branch": "02",
        "supplier_code": "000192",
        "supplier_store": "01",
    }
    payload.update(overrides)
    return service.execute(**payload)


def test_maps_repeated_codes_in_one_batch_and_keeps_order() -> None:
    service, mappings, calls = _service(
        [
            {
                "supplier_product_code": "00001234",
                "internal_product_code": "000050",
                "internal_product_description": "PARAFUSO M6",
            }
        ]
    )
    data = _execute(service)
    assert calls[0]["branch"] == "02"
    assert calls[0]["document_id"] == DOCUMENT_ID
    assert calls[0]["provider_entity_id"] == ENTITY_ID
    assert len(mappings.calls) == 1
    assert mappings.calls[0]["supplier_product_codes"] == ["00001234", "SEM-AMARRACAO"]
    assert [item["itemNumber"] for item in data["items"]] == ["1", "2", "3"]
    assert data["items"][0]["internalProductCode"] == "000050"
    assert data["items"][0]["mappingStatus"] == "mapped"
    assert data["items"][1]["internalProductCode"] == "000050"
    assert data["items"][2]["mappingStatus"] == "unmapped"
    assert data["items"][2]["internalProductCode"] is None
    assert data["summary"] == {"items": 3, "mapped": 2, "unmapped": 1, "ambiguous": 0}


def test_supplier_not_selected_does_not_call_financial_or_sa5() -> None:
    service, mappings, calls = _service([])
    data = _execute(service, supplier_code="", supplier_store="")
    assert data["productMapping"]["state"] == "supplier_required"
    assert data["items"] == []
    assert calls == []
    assert mappings.calls == []


def test_divergent_supplier_cnpj_skips_sa5() -> None:
    service, mappings, _calls = _service([], supplier_cnpj="99.999.999/0001-99")
    data = _execute(service)
    assert data["productMapping"]["state"] == "issuer_mismatch"
    assert mappings.calls == []
    assert all(item["internalProductCode"] is None for item in data["items"])
    assert all(item["mappingStatus"] is None for item in data["items"])
    assert data["items"][0]["supplierProductCode"] == "00001234"


def test_protheus_and_financial_errors_surface() -> None:
    service, _mappings, _calls = _service(None)
    with pytest.raises(InvoicePostingErpQueryError):
        _execute(service)
    broken, _mappings, _calls = _service(
        [],
        gateway_error=FinancialReceivedInvoiceGatewayError("Questor indisponível.", 503),
    )
    with pytest.raises(FinancialReceivedInvoiceGatewayError):
        _execute(broken)


def test_ambiguous_does_not_pick_a_candidate() -> None:
    service, _mappings, _calls = _service(
        [
            {
                "supplier_product_code": "00001234",
                "internal_product_code": "DELPI001",
                "internal_product_description": "UM",
            },
            {
                "supplier_product_code": "00001234",
                "internal_product_code": "DELPI999",
                "internal_product_description": "OUTRO",
            },
        ]
    )
    data = _execute(service)
    assert data["items"][0]["mappingStatus"] == "ambiguous"
    assert data["items"][0]["internalProductCode"] is None
    assert "DELPI001" not in json.dumps(data["items"][0])
    assert "DELPI999" not in json.dumps(data["items"][0])


def test_gateway_requests_nfe_detail_with_separate_entity_id() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={"success": True, "data": {"documentType": "nfe", "items": []}},
        )

    gateway = FinancialReceivedInvoiceGateway(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        base_url="http://financial-api",
        timeout_seconds=5,
        service_token="service-token",
    )
    gateway.get_nfe_detail(
        authorization="Bearer user-jwt",
        document_id=DOCUMENT_ID,
        provider_entity_id=ENTITY_ID,
        access_key=ACCESS_KEY,
        branch="01",
    )
    assert f"/invoices/received/{DOCUMENT_ID}/detail" in captured["url"]
    assert "documentType=nfe" in captured["url"]
    assert f"providerEntityId={ENTITY_ID}" in captured["url"]
    assert f"accessKey={ACCESS_KEY}" in captured["url"]
    assert "branch=01" in captured["url"]


def test_nfe_route_returns_enriched_items() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        received_fiscal_detail,
    )

    user = SimpleNamespace(
        id="u1",
        name="Ana",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_CREATE],
    )
    service = SimpleNamespace(
        execute=lambda **_kwargs: {
            "documentType": "nfe",
            "items": [{"supplierProductCode": "00001234", "mappingStatus": "mapped"}],
            "productMapping": {"state": "ready"},
        }
    )
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user), patch(
        "delpi_auth.request_context.get_request_authorization",
        return_value="Bearer user-jwt",
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_received_nfe_item_service",
        return_value=service,
    ):
        response = received_fiscal_detail(
            DOCUMENT_ID,
            branch="01",
            document_type="nfe",
            file_id="",
            access_key=ACCESS_KEY,
            provider_entity_id=ENTITY_ID,
            supplier_code="000192",
            supplier_store="01",
        )
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is True
    assert payload["data"]["items"][0]["mappingStatus"] == "mapped"
    assert payload["meta"]["operationId"] == "get_lancamento_notas_fiscais_received_nfse_detail"
