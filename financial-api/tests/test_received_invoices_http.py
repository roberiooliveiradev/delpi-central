"""Contrato HTTP de NF-e recebidas — RBAC, validação e DANFE pelo BFF."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_app.composition import financial_composer
from financial_app.domain.errors import QuestorNotConfigured
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.interface.http.routes.received_invoice_routes import router
from financial_app.application.services.received_invoices_service import ReceivedInvoicesService
from tests.conftest import full_user, user
from tests.fakes import FakeReceivedInvoiceGateway

ACCESS_KEY = "3" * 44
DOCUMENT_ID = "aabbccddeeff001122334455"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    state: dict[str, object] = {"user": full_user()}
    gateway = FakeReceivedInvoiceGateway()
    monkeypatch.setattr(
        financial_composer, "build_questor_received_invoice_gateway", lambda: gateway
    )
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = state["user"]
        return await call_next(request)

    app.include_router(router)
    test_client = TestClient(app)
    test_client.state = state  # type: ignore[attr-defined]
    test_client.invoice_gateway = gateway  # type: ignore[attr-defined]
    return test_client


def test_authorized_list_uses_the_portal_contract(client) -> None:
    response = client.get(
        "/invoices/received",
        params={"invoiceNumber": " 22844 ", "supplierCnpj": "04.252.011/0001-10", "value": "108,00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["filters"] == {
        "invoiceNumber": "22844",
        "value": "108.00",
        "supplierCnpj": "04252011000110",
    }
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["pageSize"] == 25
    assert data["pagination"]["totalItems"] == 1
    item = data["items"][0]
    assert item["documentId"] == DOCUMENT_ID
    assert item["accessKey"] == ACCESS_KEY
    assert item["invoiceNumber"] == "22844"
    assert "XmlFilename" not in item
    assert "Id" not in item
    assert item["issuerCnpj"] is None
    query = client.invoice_gateway.queries[0]
    assert isinstance(query, ReceivedInvoiceQuery)
    assert query.supplier_cnpj == "04252011000110"
    assert str(query.amount) == "108.00"
    assert not hasattr(query, "value_of")


def test_user_without_invoice_permission_receives_403(client) -> None:
    client.state["user"] = user("financial.access", "financial.view.filial-01")
    response = client.get("/invoices/received")

    assert response.status_code == 403
    assert response.json()["success"] is False
    assert client.invoice_gateway.queries == []


def test_authorized_user_downloads_pdf_from_the_bff(client) -> None:
    response = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": ACCESS_KEY},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    disposition = response.headers["content-disposition"]
    assert f'filename="NFe-{ACCESS_KEY}.pdf"' in disposition
    assert "questor" not in response.text.lower()
    assert client.invoice_gateway.downloads == [(DOCUMENT_ID, ACCESS_KEY)]


def test_invalid_document_id_and_access_key_return_422(client) -> None:
    bad_id = client.get(
        "/invoices/received/not-a-document/danfe",
        params={"accessKey": ACCESS_KEY},
    )
    bad_key = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": "123"},
    )

    assert bad_id.status_code == 422
    assert bad_key.status_code == 422
    assert client.invoice_gateway.downloads == []


def test_invalid_filters_return_422(client) -> None:
    assert client.get("/invoices/received", params={"page": 0}).status_code == 422
    assert client.get("/invoices/received", params={"pageSize": 101}).status_code == 422
    assert client.get("/invoices/received", params={"supplierCnpj": "123"}).status_code == 422
    assert client.get("/invoices/received", params={"value": "-1"}).status_code == 422
    assert client.get("/invoices/received", params={"invoiceNumber": "abc"}).status_code == 422
    assert client.invoice_gateway.queries == []


def test_unconfigured_questor_returns_503_without_leaking_secrets(client, monkeypatch) -> None:
    class ExplodingGateway:
        def list_received_invoices(self, _query: ReceivedInvoiceQuery):
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")

        def download_danfe(self, **_kwargs: object) -> bytes:
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        financial_composer, "build_questor_received_invoice_gateway", lambda: ExplodingGateway()
    )
    response = client.get("/invoices/received")

    assert response.status_code == 503
    message = response.json()["message"]
    assert "não está configurada" in message
    assert "test-questor-token" not in message
    assert "ASP.NET_SessionId" not in message


def test_service_rejects_branch_free_permission_gap() -> None:
    service = ReceivedInvoicesService(FakeReceivedInvoiceGateway())
    with pytest.raises(PermissionError):
        service.list_received(user("financial.access"), page=1, page_size=25)
