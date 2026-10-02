"""NFS-e do Questor: listagem, XML e número operacional. Sem rede."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorInvalidResponse,
)
from financial_app.domain.nfse_document_number import operational_nfse_number
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.gateways.questor_nfse_adapter import QuestorNfseAdapter
from financial_app.infrastructure.gateways.questor_received_invoice_gateway import (
    QuestorReceivedInvoiceGateway,
)
from financial_app.infrastructure.xml.nfse_standard_xml import parse_nfse_standard_xml

BASE = "https://alliance.app.questorpublico.com.br"
TOKEN = "test-questor-token"
DOCUMENT_ID = "6abf21d2ac12fe2654ee8fe9"
STANDARD_XML = """<?xml version="1.0" encoding="utf-8"?>
<Notas>
  <Nota>
    <PREFEITURA>Rio Bananal</PREFEITURA>
    <N_DA_NFSE>2600000002224</N_DA_NFSE>
    <SERIE>E</SERIE>
    <CHAVE>NFSE-CHAVE</CHAVE>
    <DATA_EMISSAO>2026-08-01</DATA_EMISSAO>
    <COMPETENCIA>2026-08</COMPETENCIA>
    <CODIGO_DE_VERIFICACAO>ABC</CODIGO_DE_VERIFICACAO>
    <NUMERO_DO_RPS>10</NUMERO_DO_RPS>
    <CODIGO_SERVICO>17.02</CODIGO_SERVICO>
    <NOME_PRESTADOR>Ação Serviços</NOME_PRESTADOR>
    <CPFCNPJ_PRESTADOR>12345678000199</CPFCNPJ_PRESTADOR>
    <NOME_TOMADOR>DELPI</NOME_TOMADOR>
    <CPFCNPJ_TOMADOR>00000000000191</CPFCNPJ_TOMADOR>
    <VL_PIS>1.00</VL_PIS>
    <VL_COFINS>2.00</VL_COFINS>
    <VL_CSLL>3.00</VL_CSLL>
    <VL_ISS>4.00</VL_ISS>
    <VL_IR>5.00</VL_IR>
    <VL_INSS>6.00</VL_INSS>
    <SERVICOS>
      <SERVICO>
        <CODIGO_SERVICO>17.02</CODIGO_SERVICO>
        <DISCRIMINACAO_DOS_SERVICOS>Manutenção</DISCRIMINACAO_DOS_SERVICOS>
        <ALIQUOTA_ISS>2.00</ALIQUOTA_ISS>
        <VALOR_DOS_SERVICOS>150.50</VALOR_DOS_SERVICOS>
        <NBS>1.1501.00</NBS>
        <VL_IBS>0.10</VL_IBS>
        <VL_CBS>0.20</VL_CBS>
      </SERVICO>
    </SERVICOS>
    <VALOR_LIQUIDO>150.50</VALOR_LIQUIDO>
    <CANCELADO>FALSE</CANCELADO>
  </Nota>
</Notas>
""".encode("utf-8")


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


def nfse_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Id": DOCUMENT_ID,
        "NumberNfse": "2600000002224",
        "EmissionDate": "2026-08-01T10:00:00Z",
        "LiquidValue": 150.5,
        "CityHall": "Rio Bananal",
        "Status": "Normal",
        "XmlOriginalFileId": "file-original",
        "XmlStandardFileId": "file-standard",
        "Provider": {
            "Name": "Prestador LTDA",
            "CPFCNPJ": "12.345.678/0001-99",
            "Mail": "secreto@prestador.example",
        },
        "Taker": {
            "Name": "DELPI COMPONENTES",
            "CPFCNPJ": "00.000.000/0001-91",
            "Mail": "tomador@delpi.example",
        },
    }
    row.update(overrides)
    return row


def _auth(request: httpx.Request, auth_calls: list[int], company_id: str = "company-01") -> httpx.Response:
    if request.url.path == "/entrarcomtoken":
        auth_calls.append(1)
        return httpx.Response(302, headers={"set-cookie": "ASP.NET_SessionId=session-test; Path=/"})
    if request.url.path == "/trocarempresa" and request.method == "POST":
        assert request.content.decode() == f"CompanyId={company_id}"
        return httpx.Response(200, text="ok")
    if request.url.path == "/autorizar":
        return httpx.Response(200, text="ok")
    raise AssertionError(f"caminho inesperado: {request.url.path}")


def _adapter(handler, *, branch: str = "01", company_id: str = "company-01", max_bytes: int = 100_000):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE, follow_redirects=True)
    session = QuestorCompanySession(
        branch_code=branch,
        company_id=company_id,
        base_url=BASE,
        api_token=TOKEN,
        client=client,
        max_bytes=max_bytes,
        sleeper=lambda _delay: None,
    )
    return QuestorNfseAdapter(session), session, client


def test_operational_number_uses_the_last_nine_digits() -> None:
    assert operational_nfse_number("1830") == "000001830"
    assert operational_nfse_number("291") == "000000291"
    assert operational_nfse_number("400502") == "000400502"
    assert operational_nfse_number("2600000002224") == "000002224"
    assert operational_nfse_number("2600000074919") == "000074919"
    assert operational_nfse_number("2600000002224") != "260000000"
    assert operational_nfse_number("2600000074919") != "260000007"
    assert operational_nfse_number("123456789") == "123456789"


def test_nfse_list_branch_01_maps_provider_taker_and_keeps_original_number() -> None:
    seen: dict[str, str] = {}
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfse/listed":
            seen["query"] = str(request.url)
            return httpx.Response(
                200,
                json={"iTotalRecords": 1, "iTotalDisplayRecords": 1, "aaData": [nfse_row()]},
            )
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler, branch="01", company_id="company-01")
    try:
        page = adapter.list_received_nfse(
            query(invoice_number="2224", supplier_cnpj="12345678000199", amount=Decimal("150.50"))
        )
    finally:
        session.close()
        client.close()

    assert "Entry=True" in seen["query"]
    assert "Number=2224" in seen["query"]
    assert "SearchCnpj=12345678000199" in seen["query"]
    assert "InitialValue=150%2C50" in seen["query"]
    assert "EndValue=150%2C50" in seen["query"]
    assert "iDisplayStart=0" in seen["query"]
    assert "sSortDir_0=desc" in seen["query"]
    assert "Mail" not in seen["query"]
    item = page.items[0]
    assert item.document_type == "nfse"
    assert item.branch_code == "01"
    assert item.provider_document_id == DOCUMENT_ID
    assert item.provider_document_number == "2600000002224"
    assert item.document_number == "000002224"
    assert item.document_match_key == "000002224"
    assert item.issuer_name == "Prestador LTDA"
    assert item.issuer_cnpj == "12345678000199"
    assert item.receiver_name == "DELPI COMPONENTES"
    assert item.receiver_cnpj == "00000000000191"
    assert item.amount == "150.5"
    assert item.city_hall == "Rio Bananal"
    assert item.printable_available is False
    assert item.xml_original_available is True
    assert item.danfe_available is False


def test_nfse_list_branch_02_and_short_number_are_padded() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfse/listed":
            return httpx.Response(
                200,
                json={
                    "iTotalRecords": 1,
                    "iTotalDisplayRecords": 1,
                    "aaData": [nfse_row(NumberNfse="1830", CityHall={"Name": "Jaraguá"})],
                },
            )
        return _auth(request, auth_calls, company_id="company-02")

    adapter, session, client = _adapter(handler, branch="02", company_id="company-02")
    try:
        item = adapter.list_received_nfse(query(page=2, page_size=10)).items[0]
    finally:
        session.close()
        client.close()

    assert item.branch_code == "02"
    assert item.provider_document_number == "1830"
    assert item.document_number == "000001830"
    assert item.city_hall == "Jaraguá"


def test_nfse_pagination_sends_display_start() -> None:
    seen: dict[str, str] = {}
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfse/listed":
            seen["query"] = str(request.url)
            return httpx.Response(200, json={"iTotalRecords": 0, "iTotalDisplayRecords": 0, "aaData": []})
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        adapter.list_received_nfse(query(page=3, page_size=25))
    finally:
        session.close()
        client.close()
    assert "iDisplayStart=50" in seen["query"]
    assert "iDisplayLength=25" in seen["query"]


def test_xml_downloads_use_document_id_not_file_ids() -> None:
    paths: list[str] = []
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/cliente/nfse/"):
            paths.append(request.url.path)
            return httpx.Response(
                200,
                headers={"content-type": "text/xml; charset=iso-8859-1"},
                content=STANDARD_XML,
            )
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        original = adapter.download_xml(document_id=DOCUMENT_ID, variant="original")
        standard = adapter.download_xml(document_id=DOCUMENT_ID, variant="standard")
    finally:
        session.close()
        client.close()

    assert paths == [
        f"/cliente/nfse/{DOCUMENT_ID}/download-xml-original",
        f"/cliente/nfse/{DOCUMENT_ID}/download-xml-standard",
    ]
    assert original == STANDARD_XML
    assert standard == STANDARD_XML
    parsed = parse_nfse_standard_xml(standard, max_bytes=len(standard))
    assert parsed.provider_name == "Ação Serviços"
    assert parsed.series == "E"
    assert parsed.services[0].nbs == "1.1501.00"
    assert parsed.services[0].ibs_cbs["VL_IBS"] == "0.10"
    assert parsed.iss == "4.00"


def test_utf8_bom_is_accepted_and_the_original_bytes_stay_intact() -> None:
    payload = b"\xef\xbb\xbf" + STANDARD_XML
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "download-xml" in request.url.path:
            return httpx.Response(200, content=payload)
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        body = adapter.download_xml(document_id=DOCUMENT_ID, variant="standard")
    finally:
        session.close()
        client.close()
    assert body == payload
    assert body.startswith(b"\xef\xbb\xbf")
    parsed = parse_nfse_standard_xml(body, max_bytes=len(body))
    assert parsed.series == "E"
    assert parsed.number == "2600000002224"


def test_html_login_with_bom_still_reauthenticates() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "download-xml" in request.url.path:
            return httpx.Response(200, content=b"\xef\xbb\xbf<html>login</html>")
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        with pytest.raises(QuestorAuthenticationError):
            adapter.download_xml(document_id=DOCUMENT_ID, variant="original")
    finally:
        session.close()
        client.close()
    assert sum(auth_calls) == 2


def test_questor_standard_root_without_notas_wrapper_is_xml() -> None:
    payload = b"""<InvoiceQuestorXmlDto>
      <PREFEITURA>Jaragua</PREFEITURA>
      <N_DA_NFSE>3639067</N_DA_NFSE>
      <SERIE>1</SERIE>
      <NOME_PRESTADOR>Prestador</NOME_PRESTADOR>
      <CPFCNPJ_PRESTADOR>12345678000199</CPFCNPJ_PRESTADOR>
      <VALOR_LIQUIDO>10.00</VALOR_LIQUIDO>
    </InvoiceQuestorXmlDto>"""
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "download-xml" in request.url.path:
            return httpx.Response(200, content=payload)
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        body = adapter.download_xml(document_id=DOCUMENT_ID, variant="standard")
    finally:
        session.close()
        client.close()
    assert body == payload
    assert sum(auth_calls) == 1
    parsed = parse_nfse_standard_xml(body, max_bytes=len(body))
    assert parsed.series == "1"
    assert parsed.provider_name == "Prestador"
    assert parsed.net_amount == "10.00"


def test_malformed_oversized_and_dtd_xml_are_rejected() -> None:
    with pytest.raises(QuestorInvalidResponse):
        parse_nfse_standard_xml(b"<?xml version='1.0'?><Notas>", max_bytes=1000)
    with pytest.raises(QuestorInvalidResponse):
        parse_nfse_standard_xml(STANDARD_XML, max_bytes=20)
    hostile = b"""<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><Notas><Nota><N_DA_NFSE>&xxe;</N_DA_NFSE></Nota></Notas>"""
    with pytest.raises(QuestorInvalidResponse):
        parse_nfse_standard_xml(hostile, max_bytes=5000)


def test_html_login_instead_of_xml_reauthenticates_then_fails() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "download-xml" in request.url.path:
            return httpx.Response(200, content=b"<html>login</html>")
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        with pytest.raises(QuestorAuthenticationError):
            adapter.download_xml(document_id=DOCUMENT_ID, variant="original")
    finally:
        session.close()
        client.close()
    assert sum(auth_calls) == 2


def test_xml_reauthentication_then_succeeds() -> None:
    auth_calls: list[int] = []
    calls = {"xml": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "download-xml" in request.url.path:
            calls["xml"] += 1
            if calls["xml"] == 1:
                return httpx.Response(401, content=b"<html>login</html>")
            return httpx.Response(200, content=STANDARD_XML)
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        body = adapter.download_xml(document_id=DOCUMENT_ID, variant="standard")
    finally:
        session.close()
        client.close()
    assert body == STANDARD_XML
    assert sum(auth_calls) == 2


def test_nfse_and_nfe_share_one_session() -> None:
    auth_calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/nfe/listagem":
            return httpx.Response(
                200,
                json={"iTotalRecords": 0, "iTotalDisplayRecords": 0, "aaData": []},
            )
        if request.url.path == "/cliente/nfse/listed":
            return httpx.Response(
                200,
                json={"iTotalRecords": 0, "iTotalDisplayRecords": 0, "aaData": []},
            )
        return _auth(request, auth_calls)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE, follow_redirects=True)
    session = QuestorCompanySession(
        branch_code="01",
        company_id="company-01",
        base_url=BASE,
        api_token=TOKEN,
        client=client,
        sleeper=lambda _delay: None,
    )
    nfe = QuestorReceivedInvoiceGateway(session=session)
    nfse = QuestorNfseAdapter(session)
    try:
        nfe.list_received_invoices(query())
        nfse.list_received_nfse(query())
    finally:
        session.close()
        client.close()
    assert sum(auth_calls) == 1


def test_branches_do_not_share_company_id() -> None:
    posted: dict[str, str] = {}

    def handler_for(company_id: str):
        auth_calls: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/trocarempresa":
                posted[company_id] = request.content.decode()
                return httpx.Response(200, text="ok")
            if request.url.path == "/cliente/nfse/listed":
                return httpx.Response(200, json={"iTotalRecords": 0, "iTotalDisplayRecords": 0, "aaData": []})
            return _auth(request, auth_calls, company_id=company_id)

        return handler

    adapters = []
    clients = []
    for branch, company in (("01", "company-01"), ("02", "company-02")):
        client = httpx.Client(
            transport=httpx.MockTransport(handler_for(company)),
            base_url=BASE,
            follow_redirects=True,
        )
        session = QuestorCompanySession(
            branch_code=branch,
            company_id=company,
            base_url=BASE,
            api_token=TOKEN,
            client=client,
            sleeper=lambda _delay: None,
        )
        adapters.append((QuestorNfseAdapter(session), session))
        clients.append(client)
    try:
        for adapter, _session in adapters:
            adapter.list_received_nfse(query())
    finally:
        for _adapter, session in adapters:
            session.close()
        for client in clients:
            client.close()
    assert posted["company-01"] == "CompanyId=company-01"
    assert posted["company-02"] == "CompanyId=company-02"
