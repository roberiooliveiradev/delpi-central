"""Parser da NF-e modelo 55 — itens, chave e recusas de XML inseguro."""

from __future__ import annotations

import pytest

from financial_app.domain.errors import InvalidReceivedInvoiceQuery, QuestorInvalidResponse
from financial_app.infrastructure.xml.cte_xml import parse_cte_xml
from financial_app.infrastructure.xml.nfe_xml import parse_nfe_xml
from financial_app.infrastructure.xml.nfse_standard_xml import parse_nfse_standard_xml

CNPJ = "12345678000199"
NS = "http://www.portalfiscal.inf.br/nfe"


def access_key(*, cnpj: str = CNPJ, number: str = "000000123", series: str = "001", model: str = "55") -> str:
    body = "42" + "2609" + cnpj + model + series + number + "1" + "12345678"
    weights = (2, 3, 4, 5, 6, 7, 8, 9)
    total = sum(int(digit) * weights[index % 8] for index, digit in enumerate(reversed(body)))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder
    return body + str(check_digit)


def nfe_xml(
    *,
    key: str | None = None,
    items: list[tuple[str, str, str, str, str]] | None = None,
    model: str = "55",
    namespaced: bool = False,
    emission: str = "2026-09-30T10:00:00-03:00",
    issuer_cnpj: str | None = None,
) -> bytes:
    key = key or access_key()
    issuer_cnpj = issuer_cnpj if issuer_cnpj is not None else key[6:20]
    rows = items if items is not None else [("1", "00001234", "PARAFUSO XYZ", "10.0000", "PC")]
    det_xml = []
    for number, code, description, quantity, unit in rows:
        det_xml.append(
            f'<det nItem="{number}"><prod>'
            f"<cProd>{code}</cProd><xProd>{description}</xProd>"
            f"<qCom>{quantity}</qCom><uCom>{unit}</uCom>"
            f"<vUnCom>1.50</vUnCom><vProd>15.00</vProd>"
            f"</prod></det>"
        )
    xmlns = f' xmlns="{NS}"' if namespaced else ""
    document = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<nfeProc{xmlns}><NFe><infNFe Id=\"NFe{key}\">"
        f"<ide><mod>{model}</mod><serie>1</serie><nNF>123</nNF><dhEmi>{emission}</dhEmi></ide>"
        f"<emit><CNPJ>{issuer_cnpj}</CNPJ><xNome>FORNECEDOR</xNome></emit>"
        f"{''.join(det_xml)}"
        f"</infNFe></NFe>"
        f"<protNFe><infProt><chNFe>{key}</chNFe></infProt></protNFe>"
        f"</nfeProc>"
    )
    return document.encode("utf-8")


def test_preserves_supplier_code_leading_zeros_and_reads_item_fields() -> None:
    key = access_key()
    parsed = parse_nfe_xml(nfe_xml(key=key, namespaced=True), max_bytes=100_000, expected_access_key=key)
    item = parsed.items[0]
    assert item.item_number == "1"
    assert item.supplier_product_code == "00001234"
    assert item.supplier_product_code != "1234"
    assert item.supplier_product_description == "PARAFUSO XYZ"
    assert item.quantity == "10.0000"
    assert item.unit == "PC"
    assert item.unit_price == "1.50"
    assert parsed.access_key == key
    assert parsed.issuer.cnpj == CNPJ
    public = parsed.as_public_dict()
    assert public["documentType"] == "nfe"
    assert public["items"][0]["supplierProductCode"] == "00001234"


def test_multiple_det_keep_order_and_special_characters() -> None:
    key = access_key()
    parsed = parse_nfe_xml(
        nfe_xml(
            key=key,
            items=[
                ("1", "057400166", "PARAFUSO", "10", "PC"),
                ("2", "ABC-12.3/4", "ARRUELA", "2", "UN"),
                ("3", "00001234", "PARAFUSO", "1", "PC"),
            ],
        ),
        max_bytes=100_000,
        expected_access_key=key,
    )
    assert [item.item_number for item in parsed.items] == ["1", "2", "3"]
    assert parsed.items[1].supplier_product_code == "ABC-12.3/4"
    assert parsed.items[2].supplier_product_code == "00001234"


@pytest.mark.parametrize(
    "payload",
    [
        b"<?xml version='1.0'?><!DOCTYPE foo [<!ELEMENT foo ANY>]><nfeProc></nfeProc>",
        b"<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><nfeProc></nfeProc>",
        b"<?xml version='1.0'?><!DOCTYPE foo [<!ATTLIST foo a CDATA 'x'>]><nfeProc></nfeProc>",
        b"<html><body>login</body></html>",
        b"isto nao e xml",
        b"",
    ],
)
def test_rejects_unsafe_or_invalid_payloads(payload: bytes) -> None:
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(payload, max_bytes=100_000, expected_access_key=access_key())


def test_rejects_divergent_access_key() -> None:
    key = access_key()
    other = access_key(number="000000124")
    with pytest.raises(InvalidReceivedInvoiceQuery, match="não confere"):
        parse_nfe_xml(nfe_xml(key=key), max_bytes=100_000, expected_access_key=other)


def test_rejects_model_other_than_55() -> None:
    key = access_key(model="65")
    with pytest.raises(InvalidReceivedInvoiceQuery, match="modelo 55"):
        parse_nfe_xml(nfe_xml(key=key, model="65"), max_bytes=100_000, expected_access_key=key)


def test_rejects_invalid_xml() -> None:
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<nfeProc><ide>", max_bytes=100_000)


def test_nfse_and_cte_parsers_remain_available() -> None:
    nfse = parse_nfse_standard_xml(
        b"<?xml version='1.0'?><Notas><Nota><SERIE>E</SERIE><N_DA_NFSE>1</N_DA_NFSE></Nota></Notas>",
        max_bytes=10_000,
    )
    assert nfse.series == "E"
    with pytest.raises(QuestorInvalidResponse):
        parse_cte_xml(b"<html></html>", max_bytes=10_000)
