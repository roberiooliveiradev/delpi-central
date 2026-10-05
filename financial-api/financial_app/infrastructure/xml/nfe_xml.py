"""NF-e modelo 55. O bytes original vai para o storage; este módulo só lê.

Namespace `http://www.portalfiscal.inf.br/nfe` é reconhecido pelo nome local.
Entidades externas, DTD e HTML são recusados antes do parse. O XML não entra em log.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date

from financial_app.domain.errors import NfeXmlRejected, QuestorInvalidResponse
from financial_app.domain.fiscal_access_key import (
    access_key_check_digit_ok,
    access_key_cnpj,
    access_key_model,
    access_key_number,
    access_key_series,
)
from financial_app.domain.services.fiscal_calendar_date import fiscal_calendar_date
from financial_app.infrastructure.xml.nfse_standard_xml import xml_inspection_sample

_SIZE_MESSAGE = "O XML da NF-e excede o tamanho máximo permitido."


@dataclass(frozen=True)
class NfeXmlDocument:
    access_key: str
    model: str
    emission_at: str
    emission_date: date
    number: str
    series: str
    issuer_cnpj: str


def parse_nfe_xml(
    payload: bytes,
    *,
    max_bytes: int,
    expected_access_key: str | None = None,
) -> NfeXmlDocument:
    _reject_unsafe_xml(payload, max_bytes=max_bytes)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise QuestorInvalidResponse("O Questor Zen devolveu um XML inválido.") from exc
    document = _read_document(root)
    if expected_access_key:
        expected = _digits(expected_access_key)
        if expected != document.access_key:
            raise NfeXmlRejected(
                "access_key_mismatch",
                "A chave da NF-e não confere com o XML.",
            )
    return document


def _reject_unsafe_xml(payload: bytes, *, max_bytes: int) -> None:
    if not payload:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if len(payload) > max_bytes:
        raise QuestorInvalidResponse(_SIZE_MESSAGE)
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
    ide = _first(inf, "ide")
    if ide is None:
        raise QuestorInvalidResponse("O XML da NF-e não traz a identificação do documento.")
    access_key = _access_key(root, inf)
    model = _text(_child(ide, "mod")) or access_key_model(access_key)
    number = _operational_number(_text(_child(ide, "nNF")), access_key)
    series = _operational_series(_text(_child(ide, "serie")), access_key)
    issuer_cnpj = _issuer_cnpj(_first(inf, "emit"), access_key)
    emission_at = _text(_child(ide, "dhEmi"))
    emission_date = fiscal_calendar_date(emission_at)
    if emission_date is None:
        raise QuestorInvalidResponse("O XML da NF-e não traz a data de emissão.")
    _require_nfe_identity(access_key=access_key, model=model)
    return NfeXmlDocument(
        access_key=access_key,
        model="55",
        emission_at=emission_at,
        emission_date=emission_date,
        number=number,
        series=series,
        issuer_cnpj=issuer_cnpj,
    )


def _require_nfe_identity(*, access_key: str, model: str) -> None:
    if len(access_key) != 44 or not access_key.isdigit():
        raise NfeXmlRejected("invalid_access_key", "A chave da NF-e é inválida.")
    if model != "55" or access_key_model(access_key) != "55":
        raise NfeXmlRejected("invalid_model", "A NF-e não é do modelo 55.")
    if not access_key_check_digit_ok(access_key):
        raise NfeXmlRejected("invalid_access_key", "O dígito verificador da NF-e é inválido.")


def _access_key(root: ET.Element, inf: ET.Element) -> str:
    from_id = _key_from_attribute(str(inf.attrib.get("Id") or ""))
    from_protocol = _digits(_text(_child(_first(root, "infProt"), "chNFe")))
    if from_id and from_protocol and from_id != from_protocol:
        raise NfeXmlRejected(
            "access_key_mismatch",
            "A chave da NF-e não confere dentro do XML.",
        )
    access_key = from_protocol or from_id
    if len(access_key) != 44:
        raise NfeXmlRejected("invalid_access_key", "A chave da NF-e é inválida.")
    return access_key


def _key_from_attribute(raw: str) -> str:
    text = raw.strip()
    if text.upper().startswith("NFE"):
        text = text[3:]
    return _digits(text)


def _operational_number(raw: str, access_key: str) -> str:
    digits = _digits(raw)
    expected = access_key_number(access_key)
    if not digits:
        return expected
    if len(digits) > 9:
        raise NfeXmlRejected("invalid_access_key", "O número da NF-e não confere com a chave.")
    normalized = digits.zfill(9)
    if expected and normalized != expected:
        raise NfeXmlRejected("invalid_access_key", "O número da NF-e não confere com a chave.")
    return normalized


def _operational_series(raw: str, access_key: str) -> str:
    digits = _digits(raw)
    expected = access_key_series(access_key)
    if not digits:
        return expected
    if len(digits) > 3:
        raise NfeXmlRejected("invalid_access_key", "A série da NF-e não confere com a chave.")
    normalized = digits.zfill(3)
    if expected and normalized != expected:
        raise NfeXmlRejected("invalid_access_key", "A série da NF-e não confere com a chave.")
    return normalized


def _issuer_cnpj(emit: ET.Element | None, access_key: str) -> str:
    found = _digits(_text(_child(emit, "CNPJ")))
    expected = access_key_cnpj(access_key)
    if found and found != expected:
        raise NfeXmlRejected("invalid_access_key", "O CNPJ do emitente não confere com a chave da NF-e.")
    return found or expected


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
