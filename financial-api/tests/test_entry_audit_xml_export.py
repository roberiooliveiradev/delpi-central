"""Exportação por período e XML por chave — contrato da auditoria de entradas."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_app.composition import financial_composer
from financial_app.domain.fiscal_access_key import access_key_check_digit_ok
from financial_app.domain.received_fiscal_document import ReceivedFiscalDocument
from financial_app.domain.received_invoice import ReceivedInvoice
from financial_app.interface.http.routes.received_invoice_routes import router
from tests.conftest import full_user, user
from tests.fakes import FakeReceivedInvoiceGateway

FILE_ID = "aabbccddeeff001122334455"
ENTITY_ID = "001122334455aabbccddeeff"
CNPJ = "04252011000110"


def _key(model: str, number: int) -> str:
    body = f"422611{CNPJ}{model}001{number:09d}100000001"
    assert len(body) == 43
    for digit in "0123456789":
        candidate = body + digit
        if access_key_check_digit_ok(candidate):
            return candidate
    raise AssertionError("dígito verificador")


NFE_KEY = _key("55", 22844)
CTE_KEY = _key("57", 24568)


def _nfe() -> ReceivedInvoice:
    return ReceivedInvoice(
        document_id=FILE_ID,
        access_key=NFE_KEY,
        invoice_number="22844",
        series="1",
        issuer_name="Fornecedor",
        issuer_cnpj=CNPJ,
        receiver_name="Empresa",
        emission_at="2026-11-12T10:00:00Z",
        amount="10.00",
        amount_formatted="R$ 10,00",
        manifestation_code="4",
        manifestation_description="Ciencia",
        danfe_available=True,
        branch_code="01",
        provider_entity_id=ENTITY_ID,
    )


def _cte() -> ReceivedFiscalDocument:
    return ReceivedFiscalDocument(
        document_type="cte",
        branch_code="01",
        provider_document_id=ENTITY_ID,
        provider_document_number="000024568",
        document_number="000024568",
        document_match_key="000024568",
        provider_document_key=CTE_KEY,
        series="001",
        issuer_name="Transportadora",
        issuer_cnpj=CNPJ,
        receiver_name="",
        receiver_cnpj=None,
        emission_at="2026-11-12T10:00:00Z",
        amount="20.00",
        amount_formatted="R$ 20,00",
        city_hall=None,
        printable_available=True,
        xml_original_available=True,
        xml_standard_available=False,
        access_key=CTE_KEY,
        provider_file_id=FILE_ID,
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    state: dict[str, object] = {"user": full_user()}
    gateway = FakeReceivedInvoiceGateway(items=(_nfe(),), cte_items=(_cte(),))
    gateway.nfe_xml = b"<?xml version='1.0'?><nfeProc><chNFe>ok</chNFe></nfeProc>"
    empty = FakeReceivedInvoiceGateway(items=(), cte_items=())
    monkeypatch.setattr(
        financial_composer,
        "build_questor_company_registry",
        lambda: type("Registry", (), {"companies": lambda self: {"01": gateway, "02": empty}})(),
    )
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = state["user"]
        return await call_next(request)

    app.include_router(router)
    test_client = TestClient(app)
    test_client.state = state  # type: ignore[attr-defined]
    test_client.gateway = gateway  # type: ignore[attr-defined]
    return test_client


PERIOD = "branch=01&issued_from=2026-11-12&issued_to=2026-11-12"


def test_export_requires_period_type_and_permission(client: TestClient) -> None:
    assert client.get("/invoices/received/export").status_code == 422
    assert client.get(f"/invoices/received/export?{PERIOD}&type=nfse").status_code == 422
    client.state["user"] = user()  # type: ignore[attr-defined]
    assert client.get(f"/invoices/received/export?{PERIOD}&type=nfe").status_code == 403


def test_export_returns_one_page_and_marks_a_short_page_complete(client: TestClient) -> None:
    response = client.get(f"/invoices/received/export?{PERIOD}&type=nfe&page=1&page_size=50")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["complete"] is True
    assert data["items"][0]["access_key"] == NFE_KEY
    assert data["items"][0]["provider_file_id"] == FILE_ID
    assert data["items"][0]["provider_document_id"] == ENTITY_ID
    assert data["items"][0]["amount"] == 10.0
    query = client.gateway.queries[-1]  # type: ignore[attr-defined]
    assert query.issued_from == date(2026, 11, 12)
    assert query.issued_to == date(2026, 11, 12)


def test_cte_export_is_the_sibling_of_nfe(client: TestClient) -> None:
    response = client.get(f"/invoices/received/export?{PERIOD}&type=cte&page_size=1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["complete"] is False
    assert data["items"][0]["access_key"] == CTE_KEY
    assert client.gateway.cte_queries[-1].issued_from == date(2026, 11, 12)  # type: ignore[attr-defined]


def test_xml_by_key_downloads_the_matching_nfe_and_rejects_the_wrong_model(client: TestClient) -> None:
    found = client.get(f"/invoices/received/by-key/{NFE_KEY}/xml?branch=01&type=nfe")
    assert found.status_code == 200
    assert found.headers["content-type"].startswith("application/xml")
    assert b"nfeProc" in found.content
    assert client.gateway.nfe_downloads == [(FILE_ID, ENTITY_ID)]  # type: ignore[attr-defined]
    wrong_model = client.get(f"/invoices/received/by-key/{NFE_KEY}/xml?branch=01&type=cte")
    assert wrong_model.status_code == 422


def test_missing_key_is_404_and_direct_nfe_xml_uses_the_same_ids(client: TestClient) -> None:
    missing = client.get(f"/invoices/received/by-key/{_key('55', 1)}/xml?branch=01&type=nfe")
    assert missing.status_code == 404
    direct = client.get(
        f"/invoices/received/{FILE_ID}/xml/original",
        params={"branch": "01", "documentType": "nfe", "providerEntityId": ENTITY_ID},
    )
    assert direct.status_code == 200
    assert b"nfeProc" in direct.content


def test_cte_lookup_sends_the_access_key(client: TestClient) -> None:
    response = client.get(f"/invoices/received/by-key/{CTE_KEY}/xml?branch=01&type=cte")
    assert response.status_code == 200
    assert b"cteProc" in response.content
    lookup = client.gateway.cte_queries[-1]  # type: ignore[attr-defined]
    assert lookup.access_key == CTE_KEY
    assert lookup.invoice_number == "24568"
