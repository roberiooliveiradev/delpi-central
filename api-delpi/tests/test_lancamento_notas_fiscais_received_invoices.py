"""Proxy de NF-e e anexo de DANFE — sem chamada real à financial-api."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.services.lancamento_notas_fiscais.danfe_storage import (
    LancamentoDanfeStorage,
)
from app.application.services.lancamento_notas_fiscais.received_invoice_attachment_service import (
    ReceivedInvoiceAttachmentService,
)
from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
)
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    InvoicePostingDuplicateError,
    InvoicePostingUpstreamError,
    InvoicePostingValidationError,
)
from app.infrastructure.gateways.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGateway,
    FinancialReceivedInvoiceGatewayError,
)

DOCUMENT_ID = "aabbccddeeff001122334455"
ACCESS_KEY = "3" * 44
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def _client(handler) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        timeout=httpx.Timeout(5.0),
    )


SERVICE_TOKEN = "test-internal-service"


def _gateway(handler, **kwargs) -> FinancialReceivedInvoiceGateway:
    return FinancialReceivedInvoiceGateway(
        client=_client(handler),
        base_url="http://financial-api:8000",
        timeout_seconds=5,
        service_token=kwargs.pop("service_token", SERVICE_TOKEN),
        sleep=lambda _seconds: None,
        **kwargs,
    )


def test_list_forwards_filters_and_authorization_without_questor_host() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["service"] = request.headers.get("x-delpi-service-token")
        captured["headers"] = " ".join(request.headers.values())
        return httpx.Response(
            200,
            json={
                "success": True,
                "message": "ok",
                "data": {
                    "items": [{"accessKey": ACCESS_KEY, "branchCode": "02"}],
                    "pagination": {"page": 1, "totalItems": 1},
                },
            },
        )

    data = _gateway(handler).list_received_invoices(
        authorization="Bearer user-jwt",
        invoice_number="22844",
        supplier_cnpj="12345678000199",
        page=2,
        page_size=25,
    )
    assert data["items"][0]["branchCode"] == "02"
    url = str(captured["url"])
    assert url.startswith("http://financial-api:8000/invoices/received?")
    assert "invoiceNumber=22844" in url
    assert "supplierCnpj=12345678000199" in url
    assert "page=2" in url
    assert "pageSize=25" in url
    assert "questorpublico" not in url
    assert captured["authorization"] is None
    assert captured["service"] == SERVICE_TOKEN
    assert "user-jwt" not in str(captured["headers"])


def test_missing_service_token_does_not_call_upstream() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("upstream não deve ser chamado")

    with pytest.raises(FinancialReceivedInvoiceGatewayError) as caught:
        _gateway(handler, service_token="").list_received_invoices(
            authorization="Bearer user-jwt",
            invoice_number="1",
            supplier_cnpj=None,
            page=1,
            page_size=25,
        )
    assert caught.value.status_code == 503
    assert "user-jwt" not in str(caught.value)
    assert SERVICE_TOKEN not in str(caught.value)


def test_financial_forbidden_is_passed_through() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"success": False, "message": "Sem permissão para consultar notas fiscais."},
        )

    with pytest.raises(FinancialReceivedInvoiceGatewayError) as caught:
        _gateway(handler).list_received_invoices(
            authorization="Bearer user-jwt",
            invoice_number="1",
            supplier_cnpj=None,
            page=1,
            page_size=25,
        )
    assert caught.value.status_code == 403
    assert "Sem permissão" in str(caught.value)


def test_invalid_pdf_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html>login</html>")

    with pytest.raises(FinancialReceivedInvoiceGatewayError) as caught:
        _gateway(handler).download_danfe(
            authorization="Bearer user-jwt",
            document_id=DOCUMENT_ID,
            access_key=ACCESS_KEY,
            branch="01",
        )
    assert caught.value.status_code == 502


def test_invalid_document_id_does_not_call_upstream() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("upstream não deve ser chamado")

    with pytest.raises(FinancialReceivedInvoiceGatewayError) as caught:
        _gateway(handler).download_danfe(
            authorization="Bearer user-jwt",
            document_id="questor-internal-id",
            access_key=ACCESS_KEY,
            branch="01",
        )
    assert caught.value.status_code == 422


def test_transient_503_is_retried() -> None:
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, headers={"Retry-After": "0"}, json={"success": False})
        return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"})

    content, filename = _gateway(handler).download_danfe(
        authorization="Bearer user-jwt",
        document_id=DOCUMENT_ID,
        access_key=ACCESS_KEY,
        branch="02",
    )
    assert content.startswith(b"%PDF")
    assert filename == f"NFe-{ACCESS_KEY}.pdf"
    assert calls["count"] == 2


def test_preview_forwards_the_origin_branch() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"})

    _gateway(handler).download_danfe(
        authorization="Bearer user-jwt",
        document_id=DOCUMENT_ID,
        access_key=ACCESS_KEY,
        branch="02",
    )
    assert "branch=02" in captured["url"]
    assert "accessKey=" in captured["url"]


def test_list_route_requires_create_permission() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        list_received_invoices,
    )

    user = SimpleNamespace(is_superadmin=False, permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_VIEW])
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            list_received_invoices(invoice_number="1", supplier_cnpj=None, page=1, page_size=25)


def test_list_route_returns_envelope() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        list_received_invoices,
    )

    user = SimpleNamespace(
        id="u1",
        name="Ana",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_CREATE],
    )
    gateway = SimpleNamespace(
        list_received_invoices=lambda **_kwargs: {"items": [{"invoiceNumber": "10"}], "pagination": {}}
    )
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user), patch(
        "delpi_auth.request_context.get_request_authorization",
        return_value="Bearer user-jwt",
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_financial_received_invoice_gateway",
        return_value=gateway,
    ):
        response = list_received_invoices(
            invoice_number="10",
            supplier_cnpj=None,
            page=1,
            page_size=25,
        )
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "list_lancamento_notas_fiscais_received_invoices"
    assert payload["data"]["items"][0]["invoiceNumber"] == "10"


def test_list_route_requires_a_filter() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        list_received_invoices,
    )

    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_CREATE],
    )
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        response = list_received_invoices(
            invoice_number="  ",
            supplier_cnpj=None,
            page=1,
            page_size=25,
            document_type=None,
        )
    payload = json.loads(response.body.decode("utf-8"))
    assert response.status_code == 422
    assert payload["success"] is False


class _Requests:
    def __init__(self) -> None:
        self.inserted = None
        self.deleted: list[str] = []

    def insert_danfe_attachment(self, **kwargs) -> None:
        self.inserted = kwargs

    def delete_request(self, request_id: str) -> None:
        self.deleted.append(request_id)


class _Create:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def execute(self, _payload, _actor):
        self.calls += 1
        if self.fail:
            raise InvoicePostingDuplicateError("Já existe.")
        return {"id": str(uuid4()), "document_number": "000012078"}


def _actor() -> Actor:
    return Actor(user_id="u1", user_name="Ana", has_create=True)


def test_received_nfe_stores_pdf_and_metadata(tmp_path) -> None:
    requests = _Requests()
    create = _Create()
    gateway = SimpleNamespace(
        download_danfe=lambda **_kwargs: (PDF, f"NFe-{ACCESS_KEY}.pdf")
    )
    service = ReceivedInvoiceAttachmentService(
        create_request=create,
        gateway=gateway,
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
    )
    created = service.execute(
        {
            "source": "received_nfe",
            "branch_code": "01",
            "source_branch": "01",
            "document_id": DOCUMENT_ID,
            "access_key": ACCESS_KEY,
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    assert create.calls == 1
    assert requests.inserted["document_id"] == DOCUMENT_ID
    assert requests.inserted["access_key"] == ACCESS_KEY
    assert (tmp_path / requests.inserted["stored_name"]).read_bytes().startswith(b"%PDF")
    assert created["danfe"]["file_name"] == f"NFe-{ACCESS_KEY}.pdf"
    assert requests.deleted == []


def test_pdf_failure_does_not_create_request() -> None:
    requests = _Requests()
    create = _Create()

    def _fail(**_kwargs):
        raise FinancialReceivedInvoiceGatewayError("O DANFE retornado não é um PDF válido.", 502)

    service = ReceivedInvoiceAttachmentService(
        create_request=create,
        gateway=SimpleNamespace(download_danfe=_fail),
        storage=LancamentoDanfeStorage("/tmp/lnf-danfe-unused"),
        requests=requests,
    )
    with pytest.raises(FinancialReceivedInvoiceGatewayError):
        service.execute(
            {
                "source": "received_nfe",
                "branch_code": "01",
                "source_branch": "01",
                "document_id": DOCUMENT_ID,
                "access_key": ACCESS_KEY,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    assert create.calls == 0
    assert requests.inserted is None


def test_duplicate_request_does_not_store_file(tmp_path) -> None:
    requests = _Requests()
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(fail=True),
        gateway=SimpleNamespace(download_danfe=lambda **_kwargs: (PDF, "NFe.pdf")),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
    )
    with pytest.raises(InvoicePostingDuplicateError):
        service.execute(
            {
                "source": "received_nfe",
                "branch_code": "01",
                "source_branch": "01",
                "document_id": DOCUMENT_ID,
                "access_key": ACCESS_KEY,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    assert list(tmp_path.iterdir()) == []
    assert requests.inserted is None


def test_store_failure_rolls_back_the_request(tmp_path) -> None:
    requests = _Requests()

    def _boom(**_kwargs):
        raise OSError("disk")

    requests.insert_danfe_attachment = _boom
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_danfe=lambda **_kwargs: (PDF, f"NFe-{ACCESS_KEY}.pdf")),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
    )
    with pytest.raises(InvoicePostingUpstreamError):
        service.execute(
            {
                "source": "received_nfe",
                "branch_code": "01",
                "source_branch": "01",
                "document_id": DOCUMENT_ID,
                "access_key": ACCESS_KEY,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    assert requests.deleted
    assert list(tmp_path.iterdir()) == []


def test_source_branch_must_match_the_request_branch(tmp_path) -> None:
    downloaded: list[str] = []

    def _download(**kwargs):
        downloaded.append(kwargs["branch"])
        return PDF, "NFe.pdf"

    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_danfe=_download),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=_Requests(),
    )
    with pytest.raises(InvoicePostingValidationError):
        service.execute(
            {
                "source": "received_nfe",
                "branch_code": "01",
                "source_branch": "02",
                "document_id": DOCUMENT_ID,
                "access_key": ACCESS_KEY,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    assert downloaded == []


def test_branch_02_danfe_is_requested_from_that_company(tmp_path) -> None:
    downloaded: list[str] = []

    def _download(**kwargs):
        downloaded.append(kwargs["branch"])
        return PDF, f"NFe-{ACCESS_KEY}.pdf"

    requests = _Requests()
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_danfe=_download),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
    )
    service.execute(
        {
            "source": "received_nfe",
            "branch_code": "02",
            "source_branch": "02",
            "document_id": DOCUMENT_ID,
            "access_key": ACCESS_KEY,
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    assert downloaded == ["02"]
    assert requests.inserted["access_key"] == ACCESS_KEY


def test_manual_create_does_not_call_the_gateway() -> None:
    create = _Create()

    def _forbidden(**_kwargs):
        raise AssertionError("gateway não deve ser chamado")

    service = ReceivedInvoiceAttachmentService(
        create_request=create,
        gateway=SimpleNamespace(download_danfe=_forbidden),
        storage=LancamentoDanfeStorage("/tmp/lnf-danfe-unused"),
        requests=_Requests(),
    )
    created = service.execute({"source": "manual"}, _actor(), authorization="")
    assert created["document_number"] == "000012078"
    assert create.calls == 1


def test_download_route_forbidden_without_branch(tmp_path) -> None:
    from fastapi.responses import JSONResponse

    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        download_request_danfe,
    )

    user = SimpleNamespace(
        id="u1",
        name="Ana",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_VIEW],
    )
    request_id = uuid4()
    detail = {
        "request": {"branch_code": "02", "created_by_user_id": "u1"},
        "danfe": {"file_name": "NFe.pdf"},
    }
    denied = JSONResponse(status_code=403, content={"success": False, "message": "Sem acesso à filial."})
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user), patch(
        "delpi_auth.request_context.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_get_invoice_posting_request_use_case",
    ) as build_get, patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router._gate_loaded_branch",
        return_value=denied,
    ):
        build_get.return_value.execute.return_value = detail
        response = download_request_danfe(request_id, disposition="attachment")
    assert response.status_code == 403


XML = b"""<?xml version="1.0" encoding="utf-8"?><Notas><Nota><SERIE>E</SERIE><N_DA_NFSE>2600000002224</N_DA_NFSE></Nota></Notas>"""
NFSE_ID = "6abf21d2ac12fe2654ee8fe9"


def test_list_forwards_document_type() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"success": True, "data": {"items": [], "pagination": {}}})

    _gateway(handler).list_received_invoices(
        authorization="Bearer user-jwt",
        invoice_number="2224",
        supplier_cnpj=None,
        page=1,
        page_size=25,
        document_type="nfse",
    )
    assert "documentType=nfse" in captured["url"]


def test_nfse_xml_download_does_not_require_access_key() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, content=XML, headers={"content-type": "text/xml"})

    content, filename = _gateway(handler).download_nfse_xml(
        authorization="Bearer user-jwt",
        document_id=NFSE_ID,
        variant="standard",
        branch="02",
    )
    assert content == XML
    assert "branch=02" in captured["url"]
    assert "accessKey" not in captured["url"]
    assert filename.endswith("-standard.xml")


def test_questor_nfse_stores_both_xml_files_and_original_number(tmp_path) -> None:
    requests = _Requests()
    requests.fiscal = []

    def insert_fiscal_attachment(**kwargs) -> None:
        requests.fiscal.append(kwargs)

    requests.insert_fiscal_attachment = insert_fiscal_attachment
    create = _Create()
    downloads: list[str] = []

    def download_nfse_xml(**kwargs):
        downloads.append(kwargs["variant"])
        return XML, f"NFSe-{kwargs['variant']}.xml"

    service = ReceivedInvoiceAttachmentService(
        create_request=create,
        gateway=SimpleNamespace(download_nfse_xml=download_nfse_xml),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
    )
    created = service.execute(
        {
            "source": "questor",
            "source_document_type": "nfse",
            "fiscal_model": "nfse",
            "branch_code": "02",
            "source_branch": "02",
            "document_id": NFSE_ID,
            "provider_document_number": "2600000002224",
            "document_number": "000002224",
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    assert downloads == ["original", "standard"]
    assert create.calls == 1
    assert {item["attachment_type"] for item in requests.fiscal} == {"xml_original", "xml_standard"}
    assert requests.fiscal[0]["provider_document_number"] == "2600000002224"
    assert requests.fiscal[0]["branch_code"] == "02"
    stored = list(tmp_path.glob("*.xml"))
    assert len(stored) == 2
    assert stored[0].read_bytes() == XML
    assert created["fiscal_attachments"][0]["provider_document_number"] == "2600000002224"


def test_nfse_branch_and_model_mismatch_are_422(tmp_path) -> None:
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_nfse_xml=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("download"))),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=_Requests(),
    )
    with pytest.raises(InvoicePostingValidationError):
        service.execute(
            {
                "source": "questor",
                "source_document_type": "nfse",
                "fiscal_model": "nfse",
                "branch_code": "01",
                "source_branch": "02",
                "document_id": NFSE_ID,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    with pytest.raises(InvoicePostingValidationError):
        service.execute(
            {
                "source": "questor",
                "source_document_type": "nfe",
                "fiscal_model": "nfse",
                "branch_code": "01",
                "source_branch": "01",
                "document_id": NFSE_ID,
            },
            _actor(),
            authorization="Bearer user-jwt",
        )


def test_nfse_second_attachment_failure_removes_the_first_file(tmp_path) -> None:
    from app.application.services.lancamento_notas_fiscais.fiscal_attachment_storage import (
        LancamentoFiscalAttachmentStorage,
    )

    requests = _Requests()
    requests.fiscal = []

    def insert_fiscal_attachment(**kwargs) -> None:
        if kwargs["attachment_type"] == "xml_standard":
            raise OSError("disk")
        requests.fiscal.append(kwargs)

    requests.insert_fiscal_attachment = insert_fiscal_attachment
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(
            download_nfse_xml=lambda **kwargs: (XML, f"{kwargs['variant']}.xml")
        ),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        fiscal_storage=LancamentoFiscalAttachmentStorage(str(tmp_path)),
        requests=requests,
    )
    with pytest.raises(InvoicePostingUpstreamError):
        service.execute(
            {
                "source": "questor",
                "source_document_type": "nfse",
                "fiscal_model": "nfse",
                "branch_code": "01",
                "source_branch": "01",
                "document_id": NFSE_ID,
                "provider_document_number": "1830",
            },
            _actor(),
            authorization="Bearer user-jwt",
        )
    assert requests.deleted
    assert list(tmp_path.glob("*.xml")) == []


def test_manual_nfse_and_cte_do_not_download_questor_files() -> None:
    create = _Create()

    def _forbidden(**_kwargs):
        raise AssertionError("gateway não deve ser chamado")

    service = ReceivedInvoiceAttachmentService(
        create_request=create,
        gateway=SimpleNamespace(download_danfe=_forbidden, download_nfse_xml=_forbidden),
        storage=LancamentoDanfeStorage("/tmp/lnf-danfe-unused"),
        requests=_Requests(),
    )
    service.execute({"source": "manual", "fiscal_model": "nfse"}, _actor(), authorization="")
    service.execute(
        {"source": "manual", "fiscal_model": "cte", "linked_invoices": []},
        _actor(),
        authorization="",
    )
    assert create.calls == 2
