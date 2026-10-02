"""Leitura do XML padronizado da NFS-e. O original em bytes não é reescrito."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from financial_app.domain.errors import QuestorInvalidResponse


@dataclass(frozen=True)
class NfseServiceLine:
    service_code: str
    description: str
    iss_rate: str
    service_amount: str
    nbs: str
    ibs_cbs: dict[str, str]


@dataclass(frozen=True)
class NfseStandardDocument:
    city_hall: str
    number: str
    series: str
    provider_key: str
    emission_date: str
    competence: str
    verification_code: str
    rps_number: str
    service_code: str
    provider_name: str
    provider_cnpj: str
    taker_name: str
    taker_cnpj: str
    pis: str
    cofins: str
    csll: str
    iss: str
    ir: str
    inss: str
    net_amount: str
    cancelled: str
    services: tuple[NfseServiceLine, ...]

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "cityHall": self.city_hall or None,
            "number": self.number or None,
            "series": self.series or None,
            "providerDocumentKey": self.provider_key or None,
            "emissionDate": self.emission_date or None,
            "competence": self.competence or None,
            "verificationCode": self.verification_code or None,
            "rpsNumber": self.rps_number or None,
            "serviceCode": self.service_code or None,
            "providerName": self.provider_name or None,
            "providerCnpj": self.provider_cnpj or None,
            "takerName": self.taker_name or None,
            "takerCnpj": self.taker_cnpj or None,
            "pis": self.pis or None,
            "cofins": self.cofins or None,
            "csll": self.csll or None,
            "iss": self.iss or None,
            "ir": self.ir or None,
            "inss": self.inss or None,
            "netAmount": self.net_amount or None,
            "cancelled": self.cancelled or None,
            "services": [
                {
                    "serviceCode": line.service_code or None,
                    "description": line.description or None,
                    "issRate": line.iss_rate or None,
                    "serviceAmount": line.service_amount or None,
                    "nbs": line.nbs or None,
                    "ibsCbs": line.ibs_cbs or None,
                }
                for line in self.services
            ],
        }


def assert_plausible_xml(payload: bytes, *, max_bytes: int) -> None:
    """Rejeita HTML, DTD e payload acima do limite antes de qualquer parse."""

    if not payload:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if len(payload) > max_bytes:
        raise QuestorInvalidResponse("O XML da NFS-e excede o tamanho máximo permitido.")
    sample = payload.lstrip()[:240].lower()
    if sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    folded = payload.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise QuestorInvalidResponse("O XML da NFS-e foi recusado por segurança.")


def parse_nfse_standard_xml(payload: bytes, *, max_bytes: int) -> NfseStandardDocument:
    assert_plausible_xml(payload, max_bytes=max_bytes)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise QuestorInvalidResponse("O Questor Zen devolveu um XML inválido.") from exc
    note = _first(root, "Nota")
    if note is None:
        note = root
    services_parent = _first(note, "Servicos")
    if services_parent is None:
        services_parent = _first(note, "SERVICOS")
    lines: list[NfseServiceLine] = []
    if services_parent is not None:
        for child in list(services_parent):
            if _local(child.tag) not in {"Servico", "SERVICO"}:
                continue
            lines.append(_service_line(child))
    return NfseStandardDocument(
        city_hall=_text(note, "PREFEITURA"),
        number=_text(note, "N_DA_NFSE"),
        series=_text(note, "SERIE"),
        provider_key=_text(note, "CHAVE"),
        emission_date=_text(note, "DATA_EMISSAO"),
        competence=_text(note, "COMPETENCIA"),
        verification_code=_text(note, "CODIGO_DE_VERIFICACAO"),
        rps_number=_text(note, "NUMERO_DO_RPS"),
        service_code=_text(note, "CODIGO_SERVICO"),
        provider_name=_text(note, "NOME_PRESTADOR"),
        provider_cnpj=_digits(_text(note, "CPFCNPJ_PRESTADOR")),
        taker_name=_text(note, "NOME_TOMADOR"),
        taker_cnpj=_digits(_text(note, "CPFCNPJ_TOMADOR")),
        pis=_text(note, "VL_PIS"),
        cofins=_text(note, "VL_COFINS"),
        csll=_text(note, "VL_CSLL"),
        iss=_text(note, "VL_ISS"),
        ir=_text(note, "VL_IR"),
        inss=_text(note, "VL_INSS"),
        net_amount=_text(note, "VALOR_LIQUIDO"),
        cancelled=_text(note, "CANCELADO"),
        services=tuple(lines),
    )


def _service_line(node: ET.Element) -> NfseServiceLine:
    extra: dict[str, str] = {}
    for child in list(node):
        name = _local(child.tag).upper()
        if "IBS" in name or "CBS" in name or name == "NBS":
            value = (child.text or "").strip()
            if value and name != "NBS":
                extra[name] = value
    return NfseServiceLine(
        service_code=_text(node, "CODIGO_SERVICO"),
        description=_text(node, "DISCRIMINACAO_DOS_SERVICOS"),
        iss_rate=_text(node, "ALIQUOTA_ISS"),
        service_amount=_text(node, "VALOR_DOS_SERVICOS"),
        nbs=_text(node, "NBS"),
        ibs_cbs=extra,
    )


def _first(node: ET.Element, name: str) -> ET.Element | None:
    wanted = name.upper()
    for child in list(node):
        if _local(child.tag).upper() == wanted:
            return child
    return None


def _text(node: ET.Element, name: str) -> str:
    found = _first(node, name)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _local(tag: str) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag
