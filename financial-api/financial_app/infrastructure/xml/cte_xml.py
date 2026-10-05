"""CT-e 4.00. O bytes original fica no storage; este módulo só lê.

Namespace `http://www.portalfiscal.inf.br/cte` é reconhecido pelo nome local,
não pelo prefixo. Entidades externas, DTD e HTML são recusados antes do parse.
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

MAX_LINKED_INVOICES = 30


@dataclass(frozen=True)
class CteParty:
    name: str
    cnpj: str


@dataclass(frozen=True)
class CtePlace:
    city: str
    state: str


@dataclass(frozen=True)
class CteLinkedInvoice:
    access_key: str
    document_number: str
    series: str


@dataclass(frozen=True)
class CteQuantity:
    unit: str
    measure: str
    quantity: str


@dataclass(frozen=True)
class CteXmlDocument:
    model: str
    series: str
    number: str
    emission_at: str
    cfop: str
    nature: str
    issuer: CteParty
    sender: CteParty
    recipient: CteParty
    origin: CtePlace
    destination: CtePlace
    service_value: str
    received_value: str
    cargo_value: str
    product: str
    access_key: str
    protocol_status: str
    protocol_reason: str
    quantities: tuple[CteQuantity, ...]
    linked_invoices: tuple[CteLinkedInvoice, ...]

    def as_public_dict(self) -> dict[str, object]:
        return {
            "documentType": "cte",
            "accessKey": self.access_key,
            "number": self.number,
            "series": self.series,
            "model": self.model,
            "emissionAt": self.emission_at or None,
            "issuer": {"name": self.issuer.name, "cnpj": self.issuer.cnpj},
            "sender": {"name": self.sender.name, "cnpj": self.sender.cnpj},
            "recipient": {"name": self.recipient.name, "cnpj": self.recipient.cnpj},
            "origin": {"city": self.origin.city, "state": self.origin.state},
            "destination": {"city": self.destination.city, "state": self.destination.state},
            "serviceValue": self.service_value or None,
            "receivedValue": self.received_value or None,
            "cargoValue": self.cargo_value or None,
            "product": self.product or None,
            "cfop": self.cfop or None,
            "nature": self.nature or None,
            "protocolStatus": self.protocol_status or None,
            "protocolReason": self.protocol_reason or None,
            "quantities": [
                {"unit": item.unit, "measure": item.measure, "quantity": item.quantity}
                for item in self.quantities
            ],
            "linkedInvoices": [
                {
                    "accessKey": item.access_key,
                    "documentNumber": item.document_number,
                    "series": item.series,
                }
                for item in self.linked_invoices
            ],
        }


def parse_cte_xml(
    payload: bytes,
    *,
    max_bytes: int,
    expected_access_key: str | None = None,
) -> CteXmlDocument:
    _reject_unsafe_xml(payload, max_bytes=max_bytes)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise QuestorInvalidResponse("O Questor Zen devolveu um XML inválido.") from exc
    document = _read_document(root)
    if expected_access_key:
        expected = re.sub(r"\D", "", expected_access_key)
        if expected != document.access_key:
            raise InvalidReceivedInvoiceQuery("A chave do CT-e não confere com o XML.")
    return document


def _reject_unsafe_xml(payload: bytes, *, max_bytes: int) -> None:
    if not payload:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if len(payload) > max_bytes:
        raise QuestorInvalidResponse("O XML do CT-e excede o tamanho máximo permitido.")
    sample = xml_inspection_sample(payload)[:240].lower()
    if sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    folded = payload.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise QuestorInvalidResponse("O XML do CT-e foi recusado por segurança.")
    if not sample.startswith(b"<"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")


def _read_document(root: ET.Element) -> CteXmlDocument:
    inf = _first(root, "infCte")
    scope = inf if inf is not None else root
    ide = _first(scope, "ide")
    if ide is None:
        raise QuestorInvalidResponse("O XML do CT-e não traz a identificação do documento.")
    emit = _party(_first(scope, "emit"))
    sender = _party(_first(scope, "rem"))
    recipient = _party(_first(scope, "dest"))
    prest = _first(scope, "vPrest")
    cargo = _first(root, "infCarga")
    protocol = _first(root, "infProt")
    access_key = _access_key(root, inf)
    number = _operational_number(_text(_child(ide, "nCT")), access_key)
    series = _operational_series(_text(_child(ide, "serie")), access_key)
    model = _text(_child(ide, "mod")) or access_key_model(access_key)
    _require_cte_identity(
        access_key=access_key,
        model=model,
        number=number,
        xml_series=_text(_child(ide, "serie")),
        issuer_cnpj=emit.cnpj,
    )
    return CteXmlDocument(
        model="57",
        series=series,
        number=number,
        emission_at=_text(_child(ide, "dhEmi")),
        cfop=_text(_child(ide, "CFOP")),
        nature=_text(_child(ide, "natOp")),
        issuer=emit,
        sender=sender,
        recipient=recipient,
        origin=CtePlace(city=_text(_child(ide, "xMunIni")), state=_text(_child(ide, "UFIni"))),
        destination=CtePlace(city=_text(_child(ide, "xMunFim")), state=_text(_child(ide, "UFFim"))),
        service_value=_decimal_text(_text(_child(prest, "vTPrest"))),
        received_value=_decimal_text(_text(_child(prest, "vRec"))),
        cargo_value=_decimal_text(_text(_child(cargo, "vCarga"))),
        product=_text(_child(cargo, "proPred")),
        access_key=access_key,
        protocol_status=_text(_child(protocol, "cStat")),
        protocol_reason=_text(_child(protocol, "xMotivo")),
        quantities=_quantities(cargo),
        linked_invoices=_linked_invoices(root),
    )


def _require_cte_identity(
    *,
    access_key: str,
    model: str,
    number: str,
    xml_series: str,
    issuer_cnpj: str,
) -> None:
    if model != "57" or access_key_model(access_key) != "57" or not access_key_check_digit_ok(access_key):
        raise InvalidReceivedInvoiceQuery("A chave do CT-e não é do modelo 57.")
    if number != access_key_number(access_key):
        raise InvalidReceivedInvoiceQuery("O número do CT-e não confere com a chave.")
    if _digits(xml_series).zfill(3) != access_key_series(access_key):
        raise InvalidReceivedInvoiceQuery("A série do CT-e não confere com a chave.")
    if _digits(issuer_cnpj) != access_key_cnpj(access_key):
        raise InvalidReceivedInvoiceQuery("O CNPJ do emitente não confere com a chave do CT-e.")


def _operational_number(nct: str, access_key: str) -> str:
    digits = _digits(nct)
    if not digits or len(digits) > 9:
        raise InvalidReceivedInvoiceQuery("O número do CT-e não confere com a chave.")
    normalized = digits.zfill(9)
    if access_key and normalized != access_key_number(access_key):
        raise InvalidReceivedInvoiceQuery("O número do CT-e não confere com a chave.")
    return normalized


def _operational_series(xml_series: str, access_key: str) -> str:
    from_key = access_key_series(access_key)
    from_xml = _digits(xml_series)
    if from_key and from_xml and from_key != from_xml.zfill(3):
        raise InvalidReceivedInvoiceQuery("A série do CT-e não confere com a chave.")
    if from_key:
        return from_key
    if not from_xml or len(from_xml) > 3:
        raise InvalidReceivedInvoiceQuery("A série do CT-e não confere com a chave.")
    return from_xml.zfill(3)


def _access_key(root: ET.Element, inf: ET.Element | None) -> str:
    protocol = _text(_child(_first(root, "infProt"), "chCTe"))
    if not protocol and inf is not None:
        raw_id = str(inf.attrib.get("Id") or "")
        protocol = raw_id[3:] if raw_id.upper().startswith("CTE") else raw_id
    digits = _digits(protocol)
    if len(digits) != 44:
        raise InvalidReceivedInvoiceQuery("A chave do CT-e não é do modelo 57.")
    return digits


def _linked_invoices(root: ET.Element) -> tuple[CteLinkedInvoice, ...]:
    found: list[CteLinkedInvoice] = []
    seen: set[str] = set()
    for node in _descendants(root, "infNFe"):
        key = _digits(_text(_child(node, "chave")))
        if not key or key in seen:
            if key in seen:
                continue
        if len(key) != 44 or access_key_model(key) != "55" or not access_key_check_digit_ok(key):
            if access_key_model(key) not in {"", "55"} and len(key) == 44:
                raise InvalidReceivedInvoiceQuery("A nota vinculada do CT-e não é uma NF-e.")
            raise InvalidReceivedInvoiceQuery("A NF-e vinculada do CT-e tem chave inválida.")
        seen.add(key)
        found.append(
            CteLinkedInvoice(
                access_key=key,
                document_number=access_key_number(key),
                series=access_key_series(key),
            )
        )
        if len(found) > MAX_LINKED_INVOICES:
            raise InvalidReceivedInvoiceQuery(
                "O CT-e traz mais de 30 NF-e vinculadas. O lançamento aceita no máximo 30."
            )
    return tuple(found)


def _quantities(cargo: ET.Element | None) -> tuple[CteQuantity, ...]:
    if cargo is None:
        return ()
    items: list[CteQuantity] = []
    for node in _children(cargo, "infQ"):
        items.append(
            CteQuantity(
                unit=_text(_child(node, "cUnid")),
                measure=_text(_child(node, "tpMed")),
                quantity=_text(_child(node, "qCarga")),
            )
        )
    return tuple(items)


def _party(node: ET.Element | None) -> CteParty:
    return CteParty(name=_text(_child(node, "xNome")), cnpj=_digits(_text(_child(node, "CNPJ"))))


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


def _descendants(node: ET.Element, name: str) -> list[ET.Element]:
    found: list[ET.Element] = []
    for child in list(node):
        if _local(child.tag) == name:
            found.append(child)
        found.extend(_descendants(child, name))
    return found


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


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return str(node.text).strip()


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _decimal_text(value: str) -> str:
    text = (value or "").strip().replace(" ", "")
    if not text:
        return ""
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return text
