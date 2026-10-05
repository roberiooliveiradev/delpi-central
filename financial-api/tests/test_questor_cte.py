"""CT-e do portal Questor: listagem Entry=0, XML, DACTE e notas vinculadas."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from financial_app.domain.errors import (
    InvalidReceivedInvoiceQuery,
    QuestorAuthenticationError,
    QuestorInvalidResponse,
    QuestorUnavailable,
)
from financial_app.domain.fiscal_access_key import access_key_check_digit_ok
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.gateways.questor_cte_adapter import QuestorCteAdapter
from financial_app.infrastructure.xml.cte_xml import parse_cte_xml

BASE = "https://questor.example"
TOKEN = "test-questor-token"
CTE_ID = "6ac06838ac12fe59b441884d"
FILE_ID = "6ac06838ac12fe59b441884b"
CTE_KEY = "35261078517588000495570400000245681618422746"
NFE_A = "35261005233912000127550010001154491427295770"
NFE_B = "35261005233912000127550010001154501021092889"


def _nfe_key(number: int) -> str:
    body = f"3526100523391200012755001{number:09d}1{number % 100_000_000:08d}"
    assert len(body) == 43
    for digit in "0123456789":
        candidate = body + digit
        if access_key_check_digit_ok(candidate):
            return candidate
    raise AssertionError("não achei DV")


def _cte_xml(
    *,
    mod: str = "57",
    serie: str = "40",
    nct: str = "24568",
    emit_cnpj: str = "78517588000495",
    access_key: str = CTE_KEY,
    linked: tuple[str, ...] | None = (NFE_A, NFE_B),
    cargo: str = "3541.40",
) -> bytes:
    notes = ""
    if linked:
        notes = "<infDoc>" + "".join(f"<infNFe><chave>{key}</chave></infNFe>" for key in linked) + "</infDoc>"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="4.00">
  <CTe><infCte Id="CTe{access_key}">
    <ide>
      <mod>{mod}</mod><serie>{serie}</serie><nCT>{nct}</nCT>
      <dhEmi>2026-10-02T10:58:37-03:00</dhEmi>
      <CFOP>5353</CFOP><natOp>Transporte</natOp>
      <xMunIni>Sao Bernardo do Campo</xMunIni><UFIni>SP</UFIni>
      <xMunFim>Jaragua do Sul</xMunFim><UFFim>SC</UFFim>
    </ide>
    <emit><CNPJ>{emit_cnpj}</CNPJ><xNome>J.J. SUL TRANSPORTES / SPO</xNome></emit>
    <rem><CNPJ>05233912000127</CNPJ><xNome>LAPP Brasil Ltda</xNome></rem>
    <dest><CNPJ>01379126000181</CNPJ><xNome>DELPI COMPONENTES LTDA</xNome></dest>
    <vPrest><vTPrest>141.08</vTPrest><vRec>141.08</vRec></vPrest>
    <infCTeNorm>
      <infCarga><vCarga>{cargo}</vCarga><proPred>COMPONENTES</proPred>
        <infQ><cUnid>01</cUnid><tpMed>PESO</tpMed><qCarga>10.0000</qCarga></infQ>
      </infCarga>
      {notes}
    </infCTeNorm>
  </infCte></CTe>
  <protCTe><infProt>
    <chCTe>{access_key}</chCTe><cStat>100</cStat><xMotivo>Autorizado</xMotivo>
  </infProt></protCTe>
</cteProc>"""
    return xml.encode("utf-8")


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Id": CTE_ID,
        "Canceled": False,
        "Taker": {"CNPJ": "78517588000495", "xNome": "J.J. SUL TRANSPORTES / SPO"},
        "TakerName": "J.J. SUL TRANSPORTES / SPO",
        "Serie": "040",
        "Key": CTE_KEY,
        "CteKey": {
            "Cnpj": "78517588000495",
            "ModelDoc": "57",
            "Serie": "040",
            "NCte": "000024568",
        },
        "Mod": "57",
        "DhEmi": "2026-10-02T03:00:00Z",
        "VtPrest": "141,08",
        "ValueFormated": "R$ 141,08",
        "XmlDacte": True,
        "XmlFilename": FILE_ID,
    }
    row.update(overrides)
    return row


def _auth(request: httpx.Request, auth_calls: list[int]) -> httpx.Response:
    if request.url.path == "/entrarcomtoken":
        auth_calls.append(1)
        return httpx.Response(302, headers={"set-cookie": "ASP.NET_SessionId=session-test; Path=/"})
    if request.url.path == "/trocarempresa":
        return httpx.Response(200, text="ok")
    if request.url.path == "/autorizar":
        return httpx.Response(200, text="ok")
    raise AssertionError(f"caminho inesperado: {request.url.path}")


def _adapter(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE, follow_redirects=True)
    session = QuestorCompanySession(
        branch_code="01",
        company_id="company-01",
        base_url=BASE,
        api_token=TOKEN,
        client=client,
        max_bytes=100_000,
        sleeper=lambda _delay: None,
    )
    return QuestorCteAdapter(session), session, client


def _query(**kwargs) -> ReceivedInvoiceQuery:
    values = {
        "invoice_number": None,
        "supplier_cnpj": None,
        "amount": None,
        "amount_text": None,
        "page": 1,
        "page_size": 25,
    }
    values.update(kwargs)
    return ReceivedInvoiceQuery(**values)


def test_list_uses_entry_zero_number_and_value_without_cnpj_filter() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/cte/listagem":
            seen["query"] = str(request.url.query)
            return httpx.Response(
                200,
                json={
                    "sEcho": "1",
                    "iTotalRecords": 3666,
                    "iTotalDisplayRecords": 3666,
                    "aaData": [_row()],
                },
            )
        return _auth(request, [])

    adapter, session, client = _adapter(handler)
    try:
        page = adapter.list_received_cte(
            _query(invoice_number="24568", supplier_cnpj="78517588000495", amount=Decimal("141.08"), page=2, page_size=10)
        )
    finally:
        session.close()
        client.close()
    query = seen["query"]
    assert "Entry=0" in query
    assert "orderGroup=DhEmi" in query
    assert "NumberCte=24568" in query
    assert "ValueOf=141%2C08" in query or "ValueOf=141,08" in query
    assert "ToValue=141" in query
    assert "SearchCnpj" not in query
    assert "iDisplayStart=10" in query
    assert "iDisplayLength=10" in query
    assert page.total_items == 3666
    item = page.items[0]
    assert item.provider_document_id == CTE_ID
    assert item.provider_file_id == FILE_ID
    assert item.provider_document_key == CTE_KEY
    assert item.document_number == "000024568"
    assert item.document_match_key == "000024568"
    assert item.series == "040"
    assert item.issuer_cnpj == "78517588000495"
    assert item.issuer_name == "J.J. SUL TRANSPORTES / SPO"
    assert item.emission_at == "2026-10-02T03:00:00Z"
    assert item.amount == "141.08"
    assert item.amount_formatted == "R$ 141,08"
    assert item.printable_available is True
    assert item.xml_original_available is True
    assert item.xml_standard_available is False
    assert item.branch_code == "01"
    assert item.document_type == "cte"


def test_listing_rejects_key_that_is_not_model_57() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/cte/listagem":
            return httpx.Response(
                200,
                json={"iTotalRecords": 1, "iTotalDisplayRecords": 1, "aaData": [_row(Key=NFE_A)]},
            )
        return _auth(request, [])

    adapter, session, client = _adapter(handler)
    try:
        page = adapter.list_received_cte(_query())
    finally:
        session.close()
        client.close()
    assert page.items == ()


def test_xml_and_dacte_use_the_two_ids_and_the_key() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/transferenciaArquivo/download":
            calls.append(str(request.url.query))
            return httpx.Response(200, content=_cte_xml(), headers={"content-type": "text/xml"})
        if request.url.path == "/cliente/cte/dactevisualizar":
            calls.append(str(request.url.query))
            return httpx.Response(200, content=b"%PDF-1.4\ncte\n", headers={"content-type": "application/pdf"})
        return _auth(request, [])

    adapter, session, client = _adapter(handler)
    try:
        xml = adapter.download_cte_xml(provider_file_id=FILE_ID, provider_document_id=CTE_ID)
        pdf = adapter.download_dacte(provider_file_id=FILE_ID, provider_document_id=CTE_ID, access_key=CTE_KEY)
    finally:
        session.close()
        client.close()
    assert "Id=6ac06838ac12fe59b441884b" in calls[0]
    assert "IdEntity=6ac06838ac12fe59b441884d" in calls[0]
    assert "number=" not in calls[0]
    assert calls[1].count("Id=") >= 1
    assert f"number={CTE_KEY}" in calls[1]
    assert xml.startswith(b"<?xml")
    assert pdf.startswith(b"%PDF")


def test_invalid_pdf_and_html_xml_are_rejected() -> None:
    def pdf_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/cte/dactevisualizar":
            return httpx.Response(200, content=b"<html>login</html>")
        return _auth(request, [])

    adapter, session, client = _adapter(pdf_handler)
    try:
        with pytest.raises(QuestorAuthenticationError):
            adapter.download_dacte(provider_file_id=FILE_ID, provider_document_id=CTE_ID, access_key=CTE_KEY)
    finally:
        session.close()
        client.close()

    def bad_pdf(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/cliente/cte/dactevisualizar":
            return httpx.Response(200, content=b"not-a-pdf")
        return _auth(request, [])

    adapter, session, client = _adapter(bad_pdf)
    try:
        with pytest.raises(QuestorInvalidResponse):
            adapter.download_dacte(provider_file_id=FILE_ID, provider_document_id=CTE_ID, access_key=CTE_KEY)
    finally:
        session.close()
        client.close()

    def html_xml(request: httpx.Request) -> httpx.Response:
        if "transferenciaArquivo" in request.url.path:
            return httpx.Response(200, content=b"<html>login</html>")
        return _auth(request, [])

    adapter, session, client = _adapter(html_xml)
    try:
        with pytest.raises(QuestorAuthenticationError):
            adapter.download_cte_xml(provider_file_id=FILE_ID, provider_document_id=CTE_ID)
    finally:
        session.close()
        client.close()


def test_xml_reauth_then_success_and_transient_retry() -> None:
    auth_calls: list[int] = []
    calls = {"xml": 0, "list": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "transferenciaArquivo" in request.url.path:
            calls["xml"] += 1
            if calls["xml"] == 1:
                return httpx.Response(401, content=b"<html>login</html>")
            return httpx.Response(200, content=_cte_xml())
        if request.url.path == "/cliente/cte/listagem":
            calls["list"] += 1
            if calls["list"] == 1:
                return httpx.Response(503, text="busy")
            return httpx.Response(200, json={"iTotalRecords": 0, "iTotalDisplayRecords": 0, "aaData": []})
        return _auth(request, auth_calls)

    adapter, session, client = _adapter(handler)
    try:
        body = adapter.download_cte_xml(provider_file_id=FILE_ID, provider_document_id=CTE_ID)
        page = adapter.list_received_cte(_query())
    finally:
        session.close()
        client.close()
    assert body.startswith(b"<?xml")
    assert page.total_items == 0
    assert calls["xml"] == 2
    assert calls["list"] == 2
    assert sum(auth_calls) >= 2


def test_download_timeout_becomes_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "transferenciaArquivo" in request.url.path:
            raise httpx.TimeoutException("slow")
        return _auth(request, [])

    adapter, session, client = _adapter(handler)
    try:
        with pytest.raises(QuestorUnavailable):
            adapter.download_cte_xml(provider_file_id=FILE_ID, provider_document_id=CTE_ID)
    finally:
        session.close()
        client.close()


def test_real_cte_extracts_parties_freight_cargo_and_linked_invoices() -> None:
    parsed = parse_cte_xml(_cte_xml(), max_bytes=100_000)
    public = parsed.as_public_dict()
    assert public["number"] == "000024568"
    assert public["series"] == "040"
    assert public["model"] == "57"
    assert public["accessKey"] == CTE_KEY
    assert public["issuer"] == {"name": "J.J. SUL TRANSPORTES / SPO", "cnpj": "78517588000495"}
    assert public["sender"] == {"name": "LAPP Brasil Ltda", "cnpj": "05233912000127"}
    assert public["recipient"] == {"name": "DELPI COMPONENTES LTDA", "cnpj": "01379126000181"}
    assert public["origin"] == {"city": "Sao Bernardo do Campo", "state": "SP"}
    assert public["destination"] == {"city": "Jaragua do Sul", "state": "SC"}
    assert public["serviceValue"] == "141.08"
    assert public["cargoValue"] == "3541.40"
    assert public["linkedInvoices"] == [
        {"accessKey": NFE_A, "documentNumber": "000115449", "series": "001"},
        {"accessKey": NFE_B, "documentNumber": "000115450", "series": "001"},
    ]


def test_linked_invoice_edges() -> None:
    empty = parse_cte_xml(_cte_xml(linked=()), max_bytes=100_000)
    assert empty.linked_invoices == ()
    duplicated = parse_cte_xml(_cte_xml(linked=(NFE_A, NFE_A, NFE_B)), max_bytes=100_000)
    assert [item.document_number for item in duplicated.linked_invoices] == ["000115449", "000115450"]
    with pytest.raises(InvalidReceivedInvoiceQuery, match="chave inválida"):
        parse_cte_xml(_cte_xml(linked=("123",)), max_bytes=100_000)
    with pytest.raises(InvalidReceivedInvoiceQuery, match="não é uma NF-e"):
        parse_cte_xml(_cte_xml(linked=(CTE_KEY,)), max_bytes=100_000)
    too_many = tuple(_nfe_key(number) for number in range(1, 32))
    with pytest.raises(InvalidReceivedInvoiceQuery, match="30"):
        parse_cte_xml(_cte_xml(linked=too_many), max_bytes=200_000)


def test_cte_identity_mismatches() -> None:
    with pytest.raises(InvalidReceivedInvoiceQuery, match="modelo 57"):
        parse_cte_xml(
            _cte_xml(mod="55", serie="001", nct="115449", emit_cnpj="05233912000127", access_key=NFE_A, linked=()),
            max_bytes=100_000,
        )
    with pytest.raises(InvalidReceivedInvoiceQuery, match="número"):
        parse_cte_xml(_cte_xml(nct="24569"), max_bytes=100_000)
    with pytest.raises(InvalidReceivedInvoiceQuery, match="série"):
        parse_cte_xml(_cte_xml(serie="99"), max_bytes=100_000)
    with pytest.raises(InvalidReceivedInvoiceQuery, match="CNPJ"):
        parse_cte_xml(_cte_xml(emit_cnpj="78517588000496"), max_bytes=100_000)
    with pytest.raises(QuestorInvalidResponse):
        parse_cte_xml(b"<html>login</html>", max_bytes=100_000)
    with pytest.raises(QuestorInvalidResponse):
        parse_cte_xml(b"<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><cteProc/>", max_bytes=100_000)
