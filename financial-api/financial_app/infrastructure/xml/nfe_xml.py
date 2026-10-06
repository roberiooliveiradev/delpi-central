"""NF-e modelo 55. Este módulo só lê o XML; não grava e não reescreve o arquivo.

O namespace `http://www.portalfiscal.inf.br/nfe` é reconhecido pelo nome local.
DTD, ENTITY, ATTLIST e HTML são recusados antes do parse. `cProd` permanece
string, com zeros à esquerda e demais caracteres do código.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from financial_app.domain.errors import InvalidReceivedInvoiceQuery, QuestorInvalidResponse
from financial_app.domain.fiscal_access_key import (
    access_key_check_digit_ok,
    access_key_cnpj,
    access_key_model,
    access_key_number,
    access_key_series,
)
from financial_app.infrastructure.xml.nfse_standard_xml import xml_inspection_sample


@dataclass(frozen=True)
class NfeParty:
    name: str
    cnpj: str


@dataclass(frozen=True)
class NfeItem:
    item_number: str
    supplier_product_code: str
    supplier_product_description: str
    quantity: str
    unit: str
    unit_price: str
    line_amount: str

    def as_public_dict(self) -> dict[str, str | None]:
        return {
            "itemNumber": self.item_number,
            "supplierProductCode": self.supplier_product_code,
            "supplierProductDescription": self.supplier_product_description,
            "quantity": self.quantity,
            "unit": self.unit,
            "unitPrice": self.unit_price or None,
            "lineAmount": self.line_amount or None,
        }


@dataclass(frozen=True)
class NfeXmlDocument:
    access_key: str
    number: str
    series: str
    model: str
    emission_at: str
    issuer: NfeParty
    items: tuple[NfeItem, ...]

    def as_public_dict(self) -> dict[str, object]:
        return {
            "documentType": "nfe",
            "accessKey": self.access_key,
            "number": self.number,
            "series": self.series,
            "model": self.model,
            "emissionAt": self.emission_at or None,
            "issuer": {"name": self.issuer.name, "cnpj": self.issuer.cnpj},
            "items": [item.as_public_dict() for item in self.items],
        }


def parse_nfe_xml(
    payload: bytes,
    *,
    max_bytes: int,
    expected_access_key: str | None = None,
) -> NfeXmlDocument:
    _reject_unsafe_xml(payload, max_bytes=max_bytes)
    try:
        root = ET.fromstring(xml_inspection_sample(payload))
    except ET.ParseError as exc:
        raise QuestorInvalidResponse("O Questor Zen devolveu um XML inválido.") from exc
    document = _read_document(root)
    if expected_access_key:
        expected = re.sub(r"\D", "", expected_access_key)
        if expected != document.access_key:
            raise InvalidReceivedInvoiceQuery("A chave da NF-e não confere com o XML.")
    return document


def _reject_unsafe_xml(payload: bytes, *, max_bytes: int) -> None:
    if not payload:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if len(payload) > max_bytes:
        raise QuestorInvalidResponse("O XML da NF-e excede o tamanho máximo permitido.")
    sample = xml_inspection_sample(payload)[:240].lower()
    if sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    folded = payload.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded or b"<!ATTLIST" in folded:
        raise QuestorInvalidResponse("O XML da NF-e foi recusado por segurança.")
    if not sample.startswith(b"<"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")


def _read_document(root: ET.Element) -> NfeXmlDocument:
    inf = _first(root, "infNFe")
    if inf is None:
        raise QuestorInvalidResponse("O XML da NF-e não traz a identificação do documento.")
    ide = _child(inf, "ide")
    if ide is None:
        raise QuestorInvalidResponse("O XML da NF-e não traz a identificação do documento.")
    emit = _party(_child(inf, "emit"))
    access_key = _access_key(root, inf)
    number = _operational_number(_text(_child(ide, "nNF")), access_key)
    series = _operational_series(_text(_child(ide, "serie")), access_key)
    model = _text(_child(ide, "mod")) or access_key_model(access_key)
    emission_at = _text(_child(ide, "dhEmi"))
    if not emission_at:
        raise InvalidReceivedInvoiceQuery("O XML da NF-e não traz a data de emissão.")
    _require_nfe_identity(
        access_key=access_key,
        model=model,
        number=number,
        xml_series=_text(_child(ide, "serie")),
        issuer_cnpj=emit.cnpj,
    )
    return NfeXmlDocument(
        access_key=access_key,
        number=number,
        series=series,
        model="55",
        emission_at=emission_at,
        issuer=emit,
        items=tuple(_items(inf)),
    )


def _require_nfe_identity(
    *,
    access_key: str,
    model: str,
    number: str,
    xml_series: str,
    issuer_cnpj: str,
) -> None:
    if model != "55" or access_key_model(access_key) != "55" or not access_key_check_digit_ok(access_key):
        raise InvalidReceivedInvoiceQuery("A chave da NF-e não é do modelo 55.")
    if number != access_key_number(access_key):
        raise InvalidReceivedInvoiceQuery("O número da NF-e não confere com a chave.")
    if _digits(xml_series).zfill(3) != access_key_series(access_key):
        raise InvalidReceivedInvoiceQuery("A série da NF-e não confere com a chave.")
    if _digits(issuer_cnpj) != access_key_cnpj(access_key):
        raise InvalidReceivedInvoiceQuery("O CNPJ do emitente não confere com a chave da NF-e.")


def _operational_number(raw_number: str, access_key: str) -> str:
    digits = _digits(raw_number)
    if not digits or len(digits) > 9:
        raise InvalidReceivedInvoiceQuery("O número da NF-e não confere com a chave.")
    normalized = digits.zfill(9)
    if access_key and normalized != access_key_number(access_key):
        raise InvalidReceivedInvoiceQuery("O número da NF-e não confere com a chave.")
    return normalized


def _operational_series(xml_series: str, access_key: str) -> str:
    from_key = access_key_series(access_key)
    from_xml = _digits(xml_series)
    if from_key and from_xml and from_key != from_xml.zfill(3):
        raise InvalidReceivedInvoiceQuery("A série da NF-e não confere com a chave.")
    if from_key:
        return from_key
    if not from_xml or len(from_xml) > 3:
        raise InvalidReceivedInvoiceQuery("A série da NF-e não confere com a chave.")
    return from_xml.zfill(3)


def _access_key(root: ET.Element, inf: ET.Element) -> str:
    protocol = _text(_child(_first(root, "infProt"), "chNFe"))
    raw_id = str(inf.attrib.get("Id") or "")
    from_id = raw_id[3:] if raw_id.upper().startswith("NFE") else raw_id
    protocol_digits = _digits(protocol)
    id_digits = _digits(from_id)
    if protocol_digits and id_digits and protocol_digits != id_digits:
        raise InvalidReceivedInvoiceQuery("A chave da NF-e não confere com o XML.")
    digits = protocol_digits or id_digits
    if len(digits) != 44:
        raise InvalidReceivedInvoiceQuery("A chave da NF-e não é do modelo 55.")
    return digits


def _items(inf: ET.Element) -> list[NfeItem]:
    found: list[NfeItem] = []
    for det in _children(inf, "det"):
        prod = _child(det, "prod")
        found.append(
            NfeItem(
                item_number=_attr(det, "nItem"),
                supplier_product_code=_code_text(_child(prod, "cProd")),
                supplier_product_description=_text(_child(prod, "xProd")),
                quantity=_text(_child(prod, "qCom")),
                unit=_text(_child(prod, "uCom")),
                unit_price=_text(_child(prod, "vUnCom")),
                line_amount=_text(_child(prod, "vProd")),
            )
        )
    return found


def _party(node: ET.Element | None) -> NfeParty:
    return NfeParty(name=_text(_child(node, "xNome")), cnpj=_digits(_text(_child(node, "CNPJ"))))


def _first(node: ET.Element | None, name: str) -> ET.Element | None:
    if node is None:
        return None
    if _local(node.tag) == name:
        return node
    for child in list(node):
        found = _first(child, name)
        if found is not None:
            return found
    return None


def _children(node: ET.Element | None, name: str) -> list[ET.Element]:
    if node is None:
        return []
    return [child for child in list(node) if _local(child.tag) == name]


def _child(node: ET.Element | None, name: str) -> ET.Element | None:
    if node is None:
        return None
    for child in list(node):
        if _local(child.tag) == name:
            return child
    return None


def _attr(node: ET.Element, name: str) -> str:
    for key, value in node.attrib.items():
        if key.rsplit("}", 1)[-1] == name:
            return str(value).strip()
    return ""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return str(node.text).strip()


def _code_text(node: ET.Element | None) -> str:
    """Remove só espaço nas pontas. Não converte número nem apaga zeros."""

    if node is None or node.text is None:
        return ""
    return str(node.text).strip()


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")
