"""Download do XML de NF-e no gateway Questor. Sem token real e sem rede."""

from __future__ import annotations

import logging

import httpx
import pytest

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorInvalidResponse,
    QuestorUnavailable,
)
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_received_invoice_gateway import (
    QuestorReceivedInvoiceGateway,
)
from nfe_xml_samples import nfe_access_key, nfe_xml

TOKEN = "test-questor-token"
BASE = "https://alliance.app.questorpublico.com.br"
SESSION_COOKIE = "session-test"
FILE_ID = "6ab797d5ac12fe368c488f35"
ENTITY_ID = "6ab797d5ac12fe368c488f37"
ACCESS_KEY = nfe_access_key()
XML = nfe_xml(ACCESS_KEY)


def _query() -> ReceivedInvoiceQuery:
    return ReceivedInvoiceQuery(
        invoice_number=None,
        supplier_cnpj=None,
        amount=None,
        amount_text=None,
        page=1,
        page_size=25,
    )


def _row() -> dict[str, object]:
    return {
        "Id": ENTITY_ID,
        "XmlFilename": FILE_ID,
        "Number": ACCESS_KEY,
        "NfeNumber": "85645",
        "Serie": "1",
        "Issuer": "FORNECEDOR",
        "Receiver": "DELPI",
        "Emission": "2026-10-02T13:00:00Z",
        "Value": 10,
        "ValueFormated": "R$ 10,00",
        "Manifestation": "",
        "ManifestationDescription": "",
        "XmlDanfe": True,
    }


def _auth(request: httpx.Request, auth_calls: list[int]) -> httpx.Response:
    path = request.url.path
    if path == "/entrarcomtoken":
        auth_calls.append(1)
        return httpx.Response(
            302,
            headers={
                "location": "/autorizar",
                "set-cookie": f"ASP.NET_SessionId={SESSION_COOKIE}; Path=/",
            },
        )
    if path == "/trocarempresa" and request.method == "POST":
        return httpx.Response(200, text="ok")
    if path == "/autorizar":
        return httpx.Response(302, headers={"location": "/cliente/painel"})
    if path == "/cliente/painel":
        return httpx.Response(200, text="painel")
    raise AssertionError(f"caminho inesperado: {path}")


def _gateway(handler, *, max_bytes: int = 100_000):
    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=BASE,
        follow_redirects=True,
        timeout=httpx.Timeout(connect=1.0, read=5.0, write=1.0, pool=1.0),
    )
    gateway = QuestorReceivedInvoiceGateway(
        branch_code="01",
        company_id="company-01",
        base_url=BASE,
        api_token=TOKEN,
        timeout_seconds=5,
        danfe_max_bytes=max_bytes,
        client=client,
        sleeper=lambda _delay: None,
    )
    return gateway, client


def test_listing_preserves_row_id_and_xml_filename_without_changing_danfe_id() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            assert request.url.params["type"] == "NFe-0"
            assert request.url.params["Entry"] == "True"
            assert request.url.params["orderGroup"] == "Emission"
            return httpx.Response(
                200,
                json={"iTotalRecords": 1, "iTotalDisplayRecords": 1, "aaData": [_row()]},
            )
        return _auth(request, auth_calls)

    gateway, client = _gateway(handler)
    try:
        public = gateway.list_received_invoices(_query()).items[0]
        exported = gateway.list_nfe_export_page(_query()).items[0]
    finally:
        gateway.close()
        client.close()

    assert public.document_id == FILE_ID
    assert public.document_id != ENTITY_ID
    assert exported.provider_file_id == FILE_ID
    assert exported.provider_entity_id == ENTITY_ID
    assert exported.access_key == ACCESS_KEY


def test_download_uses_xml_filename_as_id_and_row_id_as_entity() -> None:
    auth_calls: list[int] = []
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            captured.update(dict(request.url.params))
            return httpx.Response(
                200,
                content=XML,
                headers={
                    "content-type": "text/xml",
                    "content-disposition": 'attachment; filename="../../etc/passwd.xml"',
                },
            )
        return _auth(request, auth_calls)

    gateway, client = _gateway(handler)
    try:
        payload = gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()

    assert captured["Id"] == FILE_ID
    assert captured["IdEntity"] == ENTITY_ID
    assert captured["Id"] != captured["IdEntity"]
    assert payload == XML
    assert b"passwd" not in payload


def test_html_login_and_auth_errors_reauthenticate_without_leaking_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            return httpx.Response(200, content=b"<html>login</html>", headers={"content-type": "text/html"})
        return _auth(request, auth_calls)

    gateway, client = _gateway(handler)
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(QuestorAuthenticationError) as caught:
                gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()

    rendered = f"{caught.value}\n{caplog.text}"
    assert TOKEN not in rendered
    assert SESSION_COOKIE not in rendered
    assert "ASP.NET_SessionId" not in rendered
    assert "<html>" not in str(caught.value)
    assert sum(auth_calls) == 2
    assert "operation=nfe.xml" in caplog.text


def test_forbidden_then_valid_xml_reauthenticates_once() -> None:
    auth_calls: list[int] = []
    calls = {"xml": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            calls["xml"] += 1
            if calls["xml"] == 1:
                return httpx.Response(401, content=b"<html>login</html>")
            return httpx.Response(200, content=XML, headers={"content-type": "text/xml"})
        return _auth(request, auth_calls)

    gateway, client = _gateway(handler)
    try:
        payload = gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()

    assert payload.startswith(b"<?xml")
    assert calls["xml"] == 2
    assert sum(auth_calls) == 2


def test_timeout_and_server_errors_do_not_loop() -> None:
    auth_calls: list[int] = []
    timeouts = {"count": 0}

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            timeouts["count"] += 1
            raise httpx.TimeoutException("slow")
        return _auth(request, auth_calls)

    gateway, client = _gateway(timeout_handler)
    try:
        with pytest.raises(QuestorUnavailable):
            gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()
    assert timeouts["count"] == 3

    busy = {"count": 0}

    def busy_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            busy["count"] += 1
            return httpx.Response(503, content=b"busy")
        return _auth(request, [])

    gateway, client = _gateway(busy_handler)
    try:
        with pytest.raises(QuestorUnavailable):
            gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()
    assert busy["count"] == 3

    internal = {"count": 0}

    def internal_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            internal["count"] += 1
            return httpx.Response(500, content=b"erro")
        return _auth(request, [])

    gateway, client = _gateway(internal_handler)
    try:
        with pytest.raises(QuestorUnavailable):
            gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()
    assert internal["count"] == 1


def test_download_rejects_payloads_above_the_limit() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            return httpx.Response(200, content=b"<nfeProc>" + b"x" * 80, headers={"content-length": "90"})
        return _auth(request, auth_calls)

    gateway, client = _gateway(handler, max_bytes=32)
    try:
        with pytest.raises(QuestorInvalidResponse) as caught:
            gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()
    assert TOKEN not in str(caught.value)


def test_foreign_host_redirect_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            return httpx.Response(302, headers={"location": "https://evil.example/xml"})
        if request.url.host == "evil.example":
            return httpx.Response(200, content=XML)
        return _auth(request, [])

    gateway, client = _gateway(handler)
    try:
        with pytest.raises((QuestorInvalidResponse, QuestorUnavailable)):
            gateway.download_nfe_xml(provider_file_id=FILE_ID, provider_document_id=ENTITY_ID)
    finally:
        gateway.close()
        client.close()
