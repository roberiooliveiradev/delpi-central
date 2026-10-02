"""Contrato HTTP de NF-e recebidas — RBAC, validação e DANFE pelo BFF."""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_app.composition import financial_composer
from financial_app.middleware.auth_middleware import jwt_middleware
from financial_app.domain.errors import QuestorNotConfigured, QuestorUnavailable
from financial_app.domain.received_fiscal_document import ReceivedFiscalDocument
from financial_app.domain.received_invoice import ReceivedInvoice, ReceivedInvoiceQuery
from financial_app.interface.http.routes.received_invoice_routes import router
from financial_app.application.services.received_invoices_service import ReceivedInvoicesService
from tests.conftest import full_user, user
from tests.fakes import FakeReceivedInvoiceGateway

ACCESS_KEY = "3" * 44
DOCUMENT_ID = "aabbccddeeff001122334455"


def _invoice(
    *,
    branch_code: str,
    access_key: str,
    emission_at: str,
    document_id: str,
    invoice_number: str,
) -> ReceivedInvoice:
    return ReceivedInvoice(
        document_id=document_id,
        access_key=access_key,
        invoice_number=invoice_number,
        series="1",
        issuer_name="Fornecedor",
        issuer_cnpj=None,
        receiver_name="DELPI",
        emission_at=emission_at,
        amount="10",
        amount_formatted="R$ 10,00",
        manifestation_code="4",
        manifestation_description="Ciência",
        danfe_available=True,
        branch_code=branch_code,
    )


def _companies(
    gateway_01: FakeReceivedInvoiceGateway,
    gateway_02: FakeReceivedInvoiceGateway,
) -> dict[str, FakeReceivedInvoiceGateway]:
    return {"01": gateway_01, "02": gateway_02}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    state: dict[str, object] = {"user": full_user()}
    gateway = FakeReceivedInvoiceGateway()
    gateway_02 = FakeReceivedInvoiceGateway(items=())
    monkeypatch.setattr(
        financial_composer,
        "build_questor_company_registry",
        lambda: type(
            "Registry",
            (),
            {"companies": lambda self: _companies(gateway, gateway_02)},
        )(),
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
    test_client.invoice_gateway_02 = gateway_02  # type: ignore[attr-defined]
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
        "documentType": "all",
    }
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["pageSize"] == 25
    assert data["pagination"]["totalItems"] == 1
    item = data["items"][0]
    assert item["documentId"] == DOCUMENT_ID
    assert item["accessKey"] == ACCESS_KEY
    assert item["invoiceNumber"] == "22844"
    assert item["branchCode"] == "01"
    assert client.invoice_gateway_02.queries
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
    assert client.invoice_gateway_02.queries == []


def test_authorized_user_downloads_pdf_from_the_bff(client) -> None:
    response = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": ACCESS_KEY, "branch": "01"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    disposition = response.headers["content-disposition"]
    assert f'filename="NFe-{ACCESS_KEY}.pdf"' in disposition
    assert "questor" not in response.text.lower()
    assert client.invoice_gateway.downloads == [(DOCUMENT_ID, ACCESS_KEY)]
    assert client.invoice_gateway_02.downloads == []


def test_invalid_document_id_and_access_key_return_422(client) -> None:
    bad_id = client.get(
        "/invoices/received/not-a-document/danfe",
        params={"accessKey": ACCESS_KEY, "branch": "01"},
    )
    bad_key = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": "123", "branch": "01"},
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
        financial_composer,
        "build_questor_company_registry",
        lambda: type("Registry", (), {"companies": lambda self: {"01": ExplodingGateway(), "02": ExplodingGateway()}})(),
    )
    response = client.get("/invoices/received")

    assert response.status_code == 503
    message = response.json()["message"]
    assert "não está configurada" in message
    assert "test-questor-token" not in message
    assert "ASP.NET_SessionId" not in message


def _use(monkeypatch: pytest.MonkeyPatch, gateway_01, gateway_02) -> None:
    monkeypatch.setattr(
        financial_composer,
        "build_questor_company_registry",
        lambda: type(
            "Registry",
            (),
            {"companies": lambda self: {"01": gateway_01, "02": gateway_02}},
        )(),
    )


def test_consolidated_pages_keep_global_order(client, monkeypatch: pytest.MonkeyPatch) -> None:
    branch_01 = (
        _invoice(branch_code="01", access_key="1" * 44, emission_at="2026-05-01T00:00:00Z", document_id="a" * 24, invoice_number="501"),
        _invoice(branch_code="01", access_key="2" * 44, emission_at="2026-04-01T00:00:00Z", document_id="b" * 24, invoice_number="401"),
        _invoice(branch_code="01", access_key="3" * 44, emission_at="2026-03-01T00:00:00Z", document_id="c" * 24, invoice_number="301"),
    )
    branch_02 = (
        _invoice(branch_code="02", access_key="4" * 44, emission_at="2026-01-01T00:00:00Z", document_id="d" * 24, invoice_number="101"),
    )
    _use(monkeypatch, FakeReceivedInvoiceGateway(items=branch_01), FakeReceivedInvoiceGateway(items=branch_02))

    first = client.get("/invoices/received", params={"page": 1, "pageSize": 2})
    second = client.get("/invoices/received", params={"page": 2, "pageSize": 2})

    assert first.status_code == 200
    page_one = first.json()["data"]
    assert [item["invoiceNumber"] for item in page_one["items"]] == ["501", "401"]
    assert [item["branchCode"] for item in page_one["items"]] == ["01", "01"]
    assert page_one["pagination"] == {
        "page": 1,
        "pageSize": 2,
        "totalItems": 4,
        "totalPages": 2,
        "hasNext": True,
        "hasPrevious": False,
        "isComplete": True,
    }
    page_two = second.json()["data"]
    assert [item["invoiceNumber"] for item in page_two["items"]] == ["301", "101"]
    assert [item["branchCode"] for item in page_two["items"]] == ["01", "02"]
    assert page_two["pagination"]["hasNext"] is False
    assert page_two["pagination"]["hasPrevious"] is True


def test_same_emission_orders_by_access_key_then_branch(client, monkeypatch: pytest.MonkeyPatch) -> None:
    shared_emission = "2026-02-01T00:00:00Z"
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(items=(
            _invoice(branch_code="01", access_key="9" * 44, emission_at=shared_emission, document_id="e" * 24, invoice_number="9"),
        )),
        FakeReceivedInvoiceGateway(items=(
            _invoice(branch_code="02", access_key="1" * 44, emission_at=shared_emission, document_id="f" * 24, invoice_number="1"),
        )),
    )
    response = client.get("/invoices/received", params={"pageSize": 10})
    numbers = [item["invoiceNumber"] for item in response.json()["data"]["items"]]
    assert numbers == ["1", "9"]


def test_duplicate_access_key_is_kept_once(client, monkeypatch: pytest.MonkeyPatch) -> None:
    shared = "7" * 44
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(items=(
            _invoice(branch_code="01", access_key=shared, emission_at="2026-06-01T00:00:00Z", document_id="1" * 24, invoice_number="01"),
        )),
        FakeReceivedInvoiceGateway(items=(
            _invoice(branch_code="02", access_key=shared, emission_at="2026-01-01T00:00:00Z", document_id="2" * 24, invoice_number="02"),
        )),
    )
    data = client.get("/invoices/received").json()["data"]
    assert data["pagination"]["totalItems"] == 1
    assert data["items"][0]["branchCode"] == "01"
    assert data["items"][0]["invoiceNumber"] == "01"


def test_only_branch_02_still_requires_both_companies(client, monkeypatch: pytest.MonkeyPatch) -> None:
    gateway_01 = FakeReceivedInvoiceGateway(items=())
    gateway_02 = FakeReceivedInvoiceGateway(items=(
        _invoice(branch_code="02", access_key="5" * 44, emission_at="2026-08-01T00:00:00Z", document_id="a" * 24, invoice_number="132004"),
    ))
    _use(monkeypatch, gateway_01, gateway_02)
    data = client.get("/invoices/received", params={"invoiceNumber": "132004"}).json()["data"]
    assert data["items"][0]["branchCode"] == "02"
    assert gateway_01.queries
    assert gateway_02.queries


def test_failure_of_one_company_does_not_return_a_partial_list(client, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(),
        FakeReceivedInvoiceGateway(error=QuestorUnavailable("timeout interno")),
    )
    response = client.get("/invoices/received")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert "todas as empresas" in body["message"]
    assert "timeout interno" not in body["message"]
    assert not body.get("data")


def test_failure_of_branch_01_is_also_not_partial(client, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(error=QuestorUnavailable("falha 01")),
        FakeReceivedInvoiceGateway(),
    )
    response = client.get("/invoices/received")
    assert response.status_code == 503
    assert "todas as empresas" in response.json()["message"]


def test_danfe_uses_the_branch_session(client, monkeypatch: pytest.MonkeyPatch) -> None:
    gateway_01 = FakeReceivedInvoiceGateway(items=())
    gateway_02 = FakeReceivedInvoiceGateway(items=())
    _use(monkeypatch, gateway_01, gateway_02)
    response = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": ACCESS_KEY, "branch": "02"},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert gateway_02.downloads == [(DOCUMENT_ID, ACCESS_KEY)]
    assert gateway_01.downloads == []


def test_danfe_without_branch_or_with_unknown_branch_returns_422(client) -> None:
    missing = client.get(f"/invoices/received/{DOCUMENT_ID}/danfe", params={"accessKey": ACCESS_KEY})
    unknown = client.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": ACCESS_KEY, "branch": "03"},
    )
    assert missing.status_code == 422
    assert unknown.status_code == 422
    assert client.invoice_gateway.downloads == []
    assert client.invoice_gateway_02.downloads == []


def test_service_rejects_branch_free_permission_gap() -> None:
    service = ReceivedInvoicesService(
        {"01": FakeReceivedInvoiceGateway(), "02": FakeReceivedInvoiceGateway(items=())}
    )
    with pytest.raises(PermissionError):
        service.list_received(user("financial.access"), page=1, page_size=25)


def test_internal_reader_lists_invoices_without_financial_permissions() -> None:
    service = ReceivedInvoicesService(
        {"01": FakeReceivedInvoiceGateway(), "02": FakeReceivedInvoiceGateway(items=())}
    )
    reader = SimpleNamespace(
        principal_type="service",
        internal_invoice_reader=True,
        is_superadmin=False,
        permissions=[],
    )
    data = service.list_received(reader, page=1, page_size=25)
    assert data["items"][0]["branchCode"] == "01"


def _nfse(
    *,
    branch_code: str,
    document_id: str,
    provider_number: str,
    operational: str,
    emission_at: str,
) -> ReceivedFiscalDocument:
    return ReceivedFiscalDocument(
        document_type="nfse",
        branch_code=branch_code,
        provider_document_id=document_id,
        provider_document_number=provider_number,
        document_number=operational,
        document_match_key=operational,
        provider_document_key=None,
        series="",
        issuer_name="Prestador",
        issuer_cnpj="12345678000199",
        receiver_name="DELPI",
        receiver_cnpj=None,
        emission_at=emission_at,
        amount="10",
        amount_formatted="R$ 10,00",
        city_hall="Rio Bananal",
        printable_available=False,
        xml_original_available=True,
        xml_standard_available=True,
    )


def test_document_type_nfse_skips_nfe_and_keeps_operational_number(client, monkeypatch: pytest.MonkeyPatch) -> None:
    gateway_01 = FakeReceivedInvoiceGateway(
        items=(),
        nfse_items=(
            _nfse(
                branch_code="01",
                document_id="a" * 24,
                provider_number="2600000002224",
                operational="000002224",
                emission_at="2026-08-02T00:00:00Z",
            ),
        ),
    )
    gateway_02 = FakeReceivedInvoiceGateway(items=(), nfse_items=())
    _use(monkeypatch, gateway_01, gateway_02)
    data = client.get("/invoices/received", params={"documentType": "nfse"}).json()["data"]
    assert data["filters"]["documentType"] == "nfse"
    assert data["items"][0]["documentType"] == "nfse"
    assert data["items"][0]["branchCode"] == "01"
    assert data["items"][0]["providerDocumentNumber"] == "2600000002224"
    assert data["items"][0]["documentNumber"] == "000002224"
    assert data["items"][0]["invoiceNumber"] == "000002224"
    assert data["items"][0]["danfeAvailable"] is False
    assert gateway_01.queries == []
    assert gateway_02.queries == []
    assert gateway_01.nfse_queries


def test_document_type_nfe_ignores_nfse_failure(client, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(nfse_error=QuestorUnavailable("nfse fora")),
        FakeReceivedInvoiceGateway(items=(), nfse_error=QuestorUnavailable("nfse fora")),
    )
    response = client.get("/invoices/received", params={"documentType": "nfe"})
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["documentType"] == "nfe"


def test_nfse_failure_in_all_view_is_not_a_silent_nfe_list(client, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(nfse_error=QuestorUnavailable("nfse 01")),
        FakeReceivedInvoiceGateway(items=()),
    )
    response = client.get("/invoices/received", params={"documentType": "all"})
    assert response.status_code == 503
    assert "todas as empresas" in response.json()["message"]


def test_all_combines_types_paginates_globally_and_does_not_dedup_across_types(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared_number_nfe = _invoice(
        branch_code="01",
        access_key="8" * 44,
        emission_at="2026-07-01T00:00:00Z",
        document_id="c" * 24,
        invoice_number="000002224",
    )
    nfse_same_number = _nfse(
        branch_code="02",
        document_id="d" * 24,
        provider_number="2600000002224",
        operational="000002224",
        emission_at="2026-09-01T00:00:00Z",
    )
    older_nfse = _nfse(
        branch_code="01",
        document_id="e" * 24,
        provider_number="1830",
        operational="000001830",
        emission_at="2026-01-01T00:00:00Z",
    )
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(items=(shared_number_nfe,), nfse_items=(older_nfse,)),
        FakeReceivedInvoiceGateway(items=(), nfse_items=(nfse_same_number,)),
    )
    first = client.get("/invoices/received", params={"documentType": "all", "pageSize": 2})
    second = client.get("/invoices/received", params={"documentType": "all", "page": 2, "pageSize": 2})
    page_one = first.json()["data"]
    assert page_one["pagination"]["totalItems"] == 3
    assert [item["documentType"] for item in page_one["items"]] == ["nfse", "nfe"]
    assert page_one["items"][0]["providerDocumentNumber"] == "2600000002224"
    assert page_one["items"][1]["invoiceNumber"] == "000002224"
    page_two = second.json()["data"]
    assert [item["documentType"] for item in page_two["items"]] == ["nfse"]
    assert page_two["items"][0]["documentNumber"] == "000001830"


def test_duplicate_nfse_id_collapses_but_same_number_as_nfe_does_not(client, monkeypatch: pytest.MonkeyPatch) -> None:
    shared_id = "f" * 24
    _use(
        monkeypatch,
        FakeReceivedInvoiceGateway(
            items=(),
            nfse_items=(
                _nfse(
                    branch_code="01",
                    document_id=shared_id,
                    provider_number="291",
                    operational="000000291",
                    emission_at="2026-03-01T00:00:00Z",
                ),
            ),
        ),
        FakeReceivedInvoiceGateway(
            items=(),
            nfse_items=(
                _nfse(
                    branch_code="02",
                    document_id=shared_id,
                    provider_number="291",
                    operational="000000291",
                    emission_at="2026-02-01T00:00:00Z",
                ),
            ),
        ),
    )
    data = client.get("/invoices/received", params={"documentType": "nfse"}).json()["data"]
    assert data["pagination"]["totalItems"] == 1
    assert data["items"][0]["branchCode"] == "01"


def test_nfse_xml_download_uses_only_the_informed_branch(client, monkeypatch: pytest.MonkeyPatch) -> None:
    gateway_01 = FakeReceivedInvoiceGateway(items=())
    gateway_02 = FakeReceivedInvoiceGateway(items=())
    _use(monkeypatch, gateway_01, gateway_02)
    response = client.get(
        f"/invoices/received/{'a' * 24}/xml/original",
        params={"documentType": "nfse", "branch": "02"},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"<?xml")
    assert gateway_02.xml_downloads == [("a" * 24, "original")]
    assert gateway_01.xml_downloads == []


def test_service_token_reaches_only_received_invoices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "test-internal-service")
    gateway = FakeReceivedInvoiceGateway()
    monkeypatch.setattr(
        financial_composer,
        "build_questor_company_registry",
        lambda: type(
            "Registry",
            (),
            {
                "companies": lambda self: {
                    "01": gateway,
                    "02": FakeReceivedInvoiceGateway(items=()),
                }
            },
        )(),
    )
    app = FastAPI()
    app.middleware("http")(jwt_middleware)
    app.include_router(router)

    @app.get("/overview")
    def overview() -> dict[str, bool]:
        return {"ok": True}

    http = TestClient(app)
    headers = {"X-Delpi-Service-Token": "test-internal-service"}
    listed = http.get("/invoices/received", headers=headers)
    danfe = http.get(
        f"/invoices/received/{DOCUMENT_ID}/danfe",
        params={"accessKey": ACCESS_KEY, "branch": "01"},
        headers=headers,
    )
    blocked = http.get("/overview", headers=headers)
    wrong = http.get("/invoices/received", headers={"X-Delpi-Service-Token": "other-token"})

    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["invoiceNumber"] == "22844"
    assert danfe.status_code == 200
    assert danfe.content.startswith(b"%PDF")
    assert blocked.status_code == 403
    assert "test-internal-service" not in blocked.text
    assert "test-internal-service" not in listed.text
    assert wrong.status_code == 401
