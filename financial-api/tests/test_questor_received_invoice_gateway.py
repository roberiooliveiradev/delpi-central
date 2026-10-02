"""Questor Zen com MockTransport — sem token real e sem rede."""

from __future__ import annotations

import logging
import threading
from decimal import Decimal

import httpx
import pytest

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorNotConfigured,
    QuestorUnavailable,
)
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_received_invoice_gateway import (
    QuestorReceivedInvoiceGateway,
    _QuestorLogRedactionFilter,
    _cnpj_from_access_key,
    _exact_amount_query,
)

TOKEN = "test-questor-token"
BASE = "https://alliance.app.questorpublico.com.br"
ACCESS_KEY = "3" * 44
DOCUMENT_ID = "aabbccddeeff001122334455"
INTERNAL_ID = "questor-internal-id"
SESSION_COOKIE = "session-test"


def sample_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Id": INTERNAL_ID,
        "Issuer": "FLORICULTURA FLORISA LTDA EPP",
        "Receiver": "DELPI COMPONENTES LTDA",
        "Serie": "1",
        "Number": ACCESS_KEY,
        "NfeNumber": "22844",
        "Emission": "2026-09-30T21:40:44Z",
        "Value": 108,
        "ValueFormated": "R$ 108,00",
        "Manifestation": "4",
        "ManifestationDescription": "Ciência da Operação",
        "XmlDanfe": True,
        "XmlFilename": DOCUMENT_ID,
    }
    row.update(overrides)
    return row


def list_payload(rows: list[dict[str, object]] | None = None, total: int = 1) -> dict[str, object]:
    return {
        "iTotalRecords": total,
        "iTotalDisplayRecords": total,
        "aaData": rows if rows is not None else [sample_row()],
    }


def query(**overrides: object) -> ReceivedInvoiceQuery:
    payload = {
        "invoice_number": None,
        "supplier_cnpj": None,
        "amount": None,
        "amount_text": None,
        "page": 1,
        "page_size": 25,
    }
    payload.update(overrides)
    return ReceivedInvoiceQuery(**payload)  # type: ignore[arg-type]


def _auth_response(request: httpx.Request, auth_calls: list[int]) -> httpx.Response:
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
    if path == "/autorizar":
        return httpx.Response(302, headers={"location": "/cliente/painel"})
    if path == "/cliente/painel":
        return httpx.Response(200, text="painel")
    raise AssertionError(f"caminho inesperado: {path}")


def build_gateway(
    handler,
    *,
    api_token: str | None = TOKEN,
    danfe_max_bytes: int = 64,
    sleeper=None,
    timeout_seconds: float = 5,
) -> tuple[QuestorReceivedInvoiceGateway, httpx.Client]:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        base_url=BASE,
        follow_redirects=True,
        timeout=httpx.Timeout(connect=1.0, read=timeout_seconds, write=1.0, pool=1.0),
    )
    gateway = QuestorReceivedInvoiceGateway(
        base_url=BASE,
        api_token=api_token,
        timeout_seconds=timeout_seconds,
        danfe_max_bytes=danfe_max_bytes,
        client=client,
        sleeper=sleeper or (lambda _delay: None),
    )
    return gateway, client


def test_token_login_follows_redirects_and_reuses_the_cookie_jar() -> None:
    auth_calls: list[int] = []
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            seen["cookie"] = request.headers.get("cookie", "")
            seen["url"] = str(request.url)
            return httpx.Response(200, json=list_payload())
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        first = gateway.list_received_invoices(query())
        second = gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert first.items[0].invoice_number == "22844"
    assert second.total_items == 1
    assert sum(auth_calls) == 1
    assert f"ASP.NET_SessionId={SESSION_COOKIE}" in seen["cookie"]
    assert TOKEN not in seen["url"]
    assert "entrarcomtoken" not in seen["url"]


def test_pagination_filters_and_exact_amount_stay_inside_the_gateway() -> None:
    captured: dict[str, str] = {}
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            captured.update(dict(request.url.params))
            return httpx.Response(200, json=list_payload(total=21))
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        page = gateway.list_received_invoices(
            query(
                invoice_number="22844",
                supplier_cnpj="04.252.011/0001-10",
                amount=Decimal("108.00"),
                amount_text="108.00",
                page=3,
                page_size=10,
            )
        )
    finally:
        gateway.close()
        client.close()

    assert captured["iDisplayStart"] == "20"
    assert captured["iDisplayLength"] == "10"
    assert captured["NfeNumber"] == "22844"
    assert captured["IssuerFederalRegistration"] == "04252011000110"
    assert captured["ValueOf"] == "108,00"
    assert captured["ToValue"] == "108,00"
    assert "Value" not in captured
    assert captured["type"] == "NFe-0"
    assert captured["Entry"] == "True"
    assert page.total_items == 21
    assert _exact_amount_query(Decimal("10.50")) == {"ValueOf": "10,50", "ToValue": "10,50"}
    assert _exact_amount_query(Decimal("108")) == {"ValueOf": "108,00", "ToValue": "108,00"}
    assert _exact_amount_query(None) == {}


def test_document_id_comes_from_xml_filename_never_from_internal_id() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(
                200,
                json=list_payload(
                    rows=[sample_row(IssuerFederalRegistration="04252011000110", XmlDanfe=False)]
                ),
            )
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        item = gateway.list_received_invoices(query()).items[0]
    finally:
        gateway.close()
        client.close()

    assert item.document_id == DOCUMENT_ID
    assert item.document_id != INTERNAL_ID
    assert item.access_key == ACCESS_KEY
    assert item.invoice_number == "22844"
    assert item.series == "1"
    assert item.issuer_name == "FLORICULTURA FLORISA LTDA EPP"
    assert item.issuer_cnpj == "04252011000110"
    assert item.receiver_name == "DELPI COMPONENTES LTDA"
    assert item.emission_at == "2026-09-30T21:40:44Z"
    assert item.amount == "108"
    assert item.amount_formatted == "R$ 108,00"
    assert item.manifestation_code == "4"
    assert item.manifestation_description == "Ciência da Operação"
    assert item.danfe_available is False


def test_issuer_cnpj_stays_null_when_the_provider_omits_it() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(200, json=list_payload())
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        item = gateway.list_received_invoices(query()).items[0]
    finally:
        gateway.close()
        client.close()

    assert item.issuer_cnpj is None


def _nfe_access_key(cnpj: str) -> str:
    body = "42" + "2609" + cnpj + "55" + "001" + "000132004" + "1" + "12345678"
    weights = (2, 3, 4, 5, 6, 7, 8, 9)
    total = sum(int(digit) * weights[index % 8] for index, digit in enumerate(reversed(body)))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder
    return body + str(check_digit)


def test_issuer_cnpj_comes_from_the_access_key_when_the_list_omits_it() -> None:
    cnpj = "12345678000199"
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(200, json=list_payload(rows=[sample_row(Number=_nfe_access_key(cnpj))]))
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        item = gateway.list_received_invoices(query()).items[0]
    finally:
        gateway.close()
        client.close()

    assert item.issuer_cnpj == cnpj


def test_explicit_issuer_cnpj_wins_over_the_access_key() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(
                200,
                json=list_payload(
                    rows=[
                        sample_row(
                            Number=_nfe_access_key("12345678000199"),
                            IssuerFederalRegistration="04252011000110",
                        )
                    ]
                ),
            )
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        item = gateway.list_received_invoices(query()).items[0]
    finally:
        gateway.close()
        client.close()

    assert item.issuer_cnpj == "04252011000110"


def test_access_key_without_check_digit_does_not_yield_a_cnpj() -> None:
    broken = _nfe_access_key("12345678000199")
    broken = broken[:-1] + ("0" if broken[-1] != "0" else "1")
    assert _cnpj_from_access_key(broken) is None


def test_danfe_uses_xml_filename_and_access_key_and_accepts_pdf_magic() -> None:
    auth_calls: list[int] = []
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfe/pegarpdfdenfe"):
            captured["Id"] = request.url.params["Id"]
            captured["chNFe"] = request.url.params["chNFe"]
            return httpx.Response(
                200,
                content=b"%PDF-1.4\nfake",
                headers={"content-type": "application/octet-stream"},
            )
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        payload = gateway.download_danfe(document_id=DOCUMENT_ID, access_key=ACCESS_KEY)
    finally:
        gateway.close()
        client.close()

    assert captured["Id"] == DOCUMENT_ID
    assert captured["Id"] != INTERNAL_ID
    assert captured["chNFe"] == ACCESS_KEY
    assert payload.startswith(b"%PDF")


def test_html_body_is_not_accepted_as_pdf() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfe/pegarpdfdenfe"):
            return httpx.Response(
                200,
                content=b"<html>login secreto</html>",
                headers={"content-type": "text/html"},
            )
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        with pytest.raises(QuestorAuthenticationError) as caught:
            gateway.download_danfe(document_id=DOCUMENT_ID, access_key=ACCESS_KEY)
    finally:
        gateway.close()
        client.close()

    message = str(caught.value)
    assert "<html>" not in message
    assert TOKEN not in message
    assert SESSION_COOKIE not in message
    assert sum(auth_calls) == 2


def test_pdf_above_the_limit_is_rejected() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfe/pegarpdfdenfe"):
            return httpx.Response(
                200,
                content=b"%PDF" + b"x" * 40,
                headers={"content-type": "application/octet-stream", "content-length": "80"},
            )
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler, danfe_max_bytes=16)
    try:
        with pytest.raises(QuestorInvalidResponse) as caught:
            gateway.download_danfe(document_id=DOCUMENT_ID, access_key=ACCESS_KEY)
    finally:
        gateway.close()
        client.close()

    assert "máximo" in str(caught.value)
    assert TOKEN not in str(caught.value)


def test_pdf_body_over_the_limit_without_content_length_is_rejected() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfe/pegarpdfdenfe"):
            return httpx.Response(200, content=b"%PDF" + b"x" * 40)
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler, danfe_max_bytes=16)
    try:
        with pytest.raises(QuestorInvalidResponse):
            gateway.download_danfe(document_id=DOCUMENT_ID, access_key=ACCESS_KEY)
    finally:
        gateway.close()
        client.close()


def test_missing_danfe_returns_not_found() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfe/pegarpdfdenfe"):
            return httpx.Response(404, content=b"ausente")
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        with pytest.raises(QuestorDocumentNotFound):
            gateway.download_danfe(document_id=DOCUMENT_ID, access_key=ACCESS_KEY)
    finally:
        gateway.close()
        client.close()

    assert sum(auth_calls) == 1


def test_expired_session_reauthenticates_once() -> None:
    auth_calls: list[int] = []
    lists = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            lists["count"] += 1
            if lists["count"] == 1:
                return httpx.Response(200, content=b"<html>login</html>", headers={"content-type": "text/html"})
            return httpx.Response(200, json=list_payload())
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        page = gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert page.items[0].document_id == DOCUMENT_ID
    assert sum(auth_calls) == 2
    assert lists["count"] == 2


def test_expired_session_does_not_loop() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(401, content=b"<html>login</html>")
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        with pytest.raises(QuestorAuthenticationError):
            gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert sum(auth_calls) == 2


def test_transient_get_retries_are_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    auth_calls: list[int] = []
    delays: list[float] = []
    lists = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            lists["count"] += 1
            if lists["count"] < 3:
                return httpx.Response(503, headers={"retry-after": "1"})
            return httpx.Response(200, json=list_payload())
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler, sleeper=delays.append)
    try:
        page = gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert page.total_items == 1
    assert lists["count"] == 3
    assert len(delays) == 2
    assert all(1 <= delay <= 1.05 for delay in delays)
    assert sum(auth_calls) == 1


def test_retry_stops_after_the_attempt_budget() -> None:
    auth_calls: list[int] = []
    lists = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            lists["count"] += 1
            return httpx.Response(503)
        return _auth_response(request, auth_calls)

    gateway, client = build_gateway(handler)
    try:
        with pytest.raises(QuestorUnavailable) as caught:
            gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert lists["count"] == 3
    assert TOKEN not in str(caught.value)
    assert "entrarcomtoken" not in str(caught.value)


def test_missing_token_fails_before_any_http_call() -> None:
    called = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(500)

    gateway, client = build_gateway(handler, api_token="")
    try:
        with pytest.raises(QuestorNotConfigured) as caught:
            gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    assert called["count"] == 0
    assert TOKEN not in str(caught.value)


def test_errors_and_logs_do_not_leak_token_or_cookies(caplog: pytest.LogCaptureFixture) -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/entrarcomtoken":
            auth_calls.append(1)
            return httpx.Response(401, text="negado")
        return httpx.Response(500)

    gateway, client = build_gateway(handler)
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(QuestorAuthenticationError) as caught:
                gateway.list_received_invoices(query())
    finally:
        gateway.close()
        client.close()

    rendered = f"{caught.value}\n{caplog.text}"
    assert TOKEN not in rendered
    assert SESSION_COOKIE not in rendered
    assert "ASP.NET_SessionId" not in rendered
    assert "entrarcomtoken" not in rendered
    assert "provider=questor" in caplog.text
    assert "operation=authenticate" in caplog.text


def test_httpx_info_logs_that_carry_the_token_are_dropped(caplog: pytest.LogCaptureFixture) -> None:
    provider_logger = logging.getLogger("httpx")
    provider_logger.setLevel(logging.INFO)
    provider_logger.addFilter(_QuestorLogRedactionFilter())
    with caplog.at_level(logging.INFO, logger="httpx"):
        provider_logger.info(
            "HTTP Request: GET %s",
            BASE + "/entrarcomtoken?token=test-questor-token",
        )
        provider_logger.info("provider=questor operation=list_received_invoices status=200")
    assert TOKEN not in caplog.text
    assert "entrarcomtoken" not in caplog.text
    assert "operation=list_received_invoices" in caplog.text


def test_client_timeout_is_explicit() -> None:
    gateway = QuestorReceivedInvoiceGateway(api_token=TOKEN, timeout_seconds=12, base_url=BASE)
    try:
        client = gateway._http()
        assert client.timeout is not None
        assert client.timeout.read == 12
        assert client.timeout.connect == 10
    finally:
        gateway.close()


def test_client_user_agent_is_accepted_by_questor_nginx() -> None:
    gateway = QuestorReceivedInvoiceGateway(api_token=TOKEN, base_url=BASE)
    try:
        agent = gateway._http().headers.get("user-agent", "")
        assert agent == "MinhaDELPI-FinancialAPI/1.0"
        assert "python-httpx" not in agent.lower()
    finally:
        gateway.close()


def test_concurrent_authentication_uses_a_single_login() -> None:
    auth_calls: list[int] = []
    lock = threading.Lock()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/entrarcomtoken":
            with lock:
                auth_calls.append(1)
            return httpx.Response(
                302,
                headers={
                    "location": "/cliente/painel",
                    "set-cookie": f"ASP.NET_SessionId={SESSION_COOKIE}; Path=/",
                },
            )
        if request.url.path == "/cliente/painel":
            return httpx.Response(200, text="painel")
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(200, json=list_payload())
        return httpx.Response(404)

    gateway, client = build_gateway(handler)
    errors: list[BaseException] = []

    def work() -> None:
        try:
            gateway.list_received_invoices(query())
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(5)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        gateway.close()
        client.close()

    assert errors == []
    assert sum(auth_calls) == 1
