"""Porte de leitura.py: NF-e modelo 55, CT-e 57/67 e evento de cancelamento.

Não aplica regra fiscal. Devolve os objetos do domain.
"""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from controllership_finance_app.domain.entry_audit.models import XmlDocument, XmlItem

_NFE = "http://www.portalfiscal.inf.br/nfe"
_CTE = "http://www.portalfiscal.inf.br/cte"


def read_xml_paths(paths: list[Path]) -> tuple[dict[str, XmlDocument], dict[str, XmlDocument], int]:
    invoices: dict[str, XmlDocument] = {}
    ctes: dict[str, XmlDocument] = {}
    cancelled: set[str] = set()
    ignored = 0
    for name, payload in _iter_bytes(paths):
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            ignored += 1
            continue
        if _find(root, _CTE, "infEvento") is not None and _find(root, _CTE, "infCte") is None:
            if _text(root, _CTE, ".//infEvento/tpEvento") == "110111":
                cancelled.add(_text(root, _CTE, ".//infEvento/chCTe"))
            continue
        if _find(root, _CTE, "infCte") is not None:
            document = _cte(root)
            if document is None:
                ignored += 1
            else:
                ctes[document.access_key] = document
            continue
        if _find(root, _NFE, "infEvento") is not None and _find(root, _NFE, "infNFe") is None:
            if _text(root, _NFE, ".//infEvento/tpEvento") == "110111":
                cancelled.add(_text(root, _NFE, ".//infEvento/chNFe"))
            continue
        if _find(root, _NFE, "infNFe") is None or _text(root, _NFE, ".//ide/mod") != "55":
            ignored += 1
            continue
        document = _nfe(root)
        if document is None:
            ignored += 1
        else:
            invoices[document.access_key] = document
    for key in cancelled:
        _mark_cancelled(invoices, key)
        _mark_cancelled(ctes, key)
    return invoices, ctes, ignored


def _mark_cancelled(documents: dict[str, XmlDocument], key: str) -> None:
    current = documents.get(key)
    if current is None:
        return
    documents[key] = XmlDocument(**{**current.__dict__, "cancelled": True})


def _iter_bytes(paths: list[Path]):
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.suffix.lower() == ".xml":
                    yield child.name, child.read_bytes()
                elif child.suffix.lower() == ".zip":
                    yield from _iter_bytes([child])
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.lower().endswith(".xml"):
                        yield name, archive.read(name)
        elif path.suffix.lower() == ".xml":
            yield path.name, path.read_bytes()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(root: ET.Element, namespace: str, name: str) -> ET.Element | None:
    return root.find(f".//{{{namespace}}}{name}")


def _text(root: ET.Element, namespace: str, path: str) -> str:
    # path uses local names separated the same way ElementTree accepts with a namespace prefix map.
    element = root.find(_qualify(path, namespace))
    return (element.text or "").strip() if element is not None and element.text else ""


def _qualify(path: str, namespace: str) -> str:
    parts = []
    for piece in path.split("/"):
        if piece in {"", ".", ".."} or piece.startswith("."):
            parts.append(piece)
            continue
        if piece.startswith("{"):
            parts.append(piece)
        else:
            parts.append(f"{{{namespace}}}{piece}" if not piece.startswith(".") else piece)
    # The helper only qualifies plain names. Rebuild simple './/a/b' paths.
    if path.startswith(".//"):
        tail = "/".join(f"{{{namespace}}}{part}" for part in path[3:].split("/"))
        return ".//" + tail
    return "/".join(f"{{{namespace}}}{part}" for part in path.split("/") if part)


def _num(root: ET.Element, namespace: str, path: str) -> float:
    raw = _text(root, namespace, path)
    try:
        return float(raw) if raw else 0.0
    except ValueError:
        return 0.0


def _when(value: str) -> datetime | None:
    text = (value or "")[:19]
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _nfe(root: ET.Element) -> XmlDocument | None:
    info = _find(root, _NFE, "infNFe")
    if info is None:
        return None
    access_key = (info.attrib.get("Id") or "")[3:]
    if len(access_key) != 44:
        return None
    crt = _text(root, _NFE, ".//emit/CRT")
    items: list[XmlItem] = []
    for detail in root.iter(f"{{{_NFE}}}det"):
        icms = None
        for child in detail.iter(f"{{{_NFE}}}ICMS"):
            for node in list(child):
                icms = node
                break
        ipi_amount = _child_num(detail, "IPITrib", "vIPI") + _child_num(detail, "IPI", "vIPIDevol")
        items.append(
            XmlItem(
                number=int(detail.attrib.get("nItem") or 0),
                product_code=_child_text(detail, "prod", "cProd"),
                description=_child_text(detail, "prod", "xProd"),
                ncm=_child_text(detail, "prod", "NCM"),
                cfop=_child_text(detail, "prod", "CFOP"),
                amount=_child_num(detail, "prod", "vProd"),
                origin=_child_text(icms, "", "orig") if icms is not None else "",
                cst=_child_text(icms, "", "CST") if icms is not None else "",
                csosn=_child_text(icms, "", "CSOSN") if icms is not None else "",
                icms_base=_child_num(icms, "", "vBC") if icms is not None else 0.0,
                icms_rate=_child_num(icms, "", "pICMS") if icms is not None else 0.0,
                icms_amount=_child_num(icms, "", "vICMS") if icms is not None else 0.0,
                ipi_amount=ipi_amount,
                ipi_base=_child_num(detail, "IPITrib", "vBC"),
                ipi_rate=_child_num(detail, "IPITrib", "pIPI"),
                st_amount=_child_num(icms, "", "vICMSST") if icms is not None else 0.0,
                simple_credit=_child_num(icms, "", "vCredICMSSN") if icms is not None else 0.0,
                simple_rate=_child_num(icms, "", "pCredSN") if icms is not None else 0.0,
                discount=_child_num(detail, "prod", "vDesc"),
                other_amount=_child_num(detail, "prod", "vOutro"),
            )
        )
    direction = "Entrada" if _text(root, _NFE, ".//ide/tpNF") == "0" else "Saída"
    return XmlDocument(
        access_key=access_key,
        model="55",
        number=int(_text(root, _NFE, ".//ide/nNF") or 0),
        series=_text(root, _NFE, ".//ide/serie"),
        issued_at=_when(_text(root, _NFE, ".//ide/dhEmi") or _text(root, _NFE, ".//ide/dEmi")),
        issuer_tax_id=_text(root, _NFE, ".//emit/CNPJ") or _text(root, _NFE, ".//emit/CPF"),
        issuer_name=_text(root, _NFE, ".//emit/xNome"),
        issuer_state=_text(root, _NFE, ".//emit/enderEmit/UF"),
        recipient_tax_id=_text(root, _NFE, ".//dest/CNPJ") or _text(root, _NFE, ".//dest/CPF"),
        direction=direction,
        crt=crt,
        goods_amount=_num(root, _NFE, ".//ICMSTot/vProd"),
        freight_amount=_num(root, _NFE, ".//ICMSTot/vFrete"),
        discount_amount=_num(root, _NFE, ".//ICMSTot/vDesc"),
        other_amount=_num(root, _NFE, ".//ICMSTot/vOutro"),
        icms_base=_num(root, _NFE, ".//ICMSTot/vBC"),
        icms_amount=_num(root, _NFE, ".//ICMSTot/vICMS"),
        st_amount=_num(root, _NFE, ".//ICMSTot/vST"),
        ipi_amount=_num(root, _NFE, ".//ICMSTot/vIPI"),
        total_amount=_num(root, _NFE, ".//ICMSTot/vNF"),
        status_code=_text(root, _NFE, ".//protNFe/infProt/cStat"),
        items=tuple(items),
    )


def _cte(root: ET.Element) -> XmlDocument | None:
    info = _find(root, _CTE, "infCte")
    if info is None:
        return None
    access_key = (info.attrib.get("Id") or "")[3:]
    if len(access_key) != 44:
        return None
    icms_node = None
    group = ""
    for node in root.iter(f"{{{_CTE}}}ICMS"):
        for child in list(node):
            icms_node = child
            group = _local(child.tag)
            break
    cst = _child_text(icms_node, "", "CST") if icms_node is not None else ""
    base = _child_num(icms_node, "", "vBC") if icms_node is not None else 0.0
    rate = _child_num(icms_node, "", "pICMS") if icms_node is not None else 0.0
    amount = _child_num(icms_node, "", "vICMS") if icms_node is not None else 0.0
    if group == "ICMSOutraUF" and icms_node is not None:
        cst = cst or "90"
        base = _child_num(icms_node, "", "vBCOutraUF")
        rate = _child_num(icms_node, "", "pICMSOutraUF")
        amount = _child_num(icms_node, "", "vICMSOutraUF")
    elif group == "ICMS60" and icms_node is not None:
        base = _child_num(icms_node, "", "vBCSTRet")
        rate = _child_num(icms_node, "", "pICMSSTRet")
        amount = _child_num(icms_node, "", "vICMSSTRet")
    elif group == "ICMSSN":
        cst = cst or "90"
        base = rate = amount = 0.0
    taker_code = _text(root, _CTE, ".//ide/toma3/toma") or _text(root, _CTE, ".//ide/toma03/toma")
    role = {"0": "rem", "1": "exped", "2": "receb", "3": "dest"}.get(taker_code, "")
    taker_tax_id = _party(root, role) if role else (
        _text(root, _CTE, ".//ide/toma4/CNPJ") or _text(root, _CTE, ".//ide/toma4/CPF")
    )
    service = _num(root, _CTE, ".//vPrest/vTPrest")
    linked = tuple(
        (node.text or "").strip()
        for node in root.iter(f"{{{_CTE}}}chave")
        if (node.text or "").strip()
    )
    return XmlDocument(
        access_key=access_key,
        model=_text(root, _CTE, ".//ide/mod") or "57",
        number=int(_text(root, _CTE, ".//ide/nCT") or 0),
        series=_text(root, _CTE, ".//ide/serie"),
        issued_at=_when(_text(root, _CTE, ".//ide/dhEmi")),
        issuer_tax_id=_text(root, _CTE, ".//emit/CNPJ") or _text(root, _CTE, ".//emit/CPF"),
        issuer_name=_text(root, _CTE, ".//emit/xNome"),
        issuer_state=_text(root, _CTE, ".//emit/enderEmit/UF"),
        recipient_tax_id=_party(root, "dest"),
        direction="CT-e",
        crt=_text(root, _CTE, ".//emit/CRT"),
        goods_amount=0.0,
        freight_amount=0.0,
        discount_amount=0.0,
        other_amount=0.0,
        icms_base=base,
        icms_amount=amount,
        st_amount=0.0,
        ipi_amount=0.0,
        total_amount=service,
        status_code=_text(root, _CTE, ".//protCTe/infProt/cStat"),
        service_amount=service,
        cfop=_text(root, _CTE, ".//ide/CFOP"),
        origin_state=_text(root, _CTE, ".//ide/UFIni"),
        destination_state=_text(root, _CTE, ".//ide/UFFim"),
        taker_tax_id=taker_tax_id,
        icms_rate=rate,
        cst=cst,
        simples_national=group == "ICMSSN",
        substituted=group == "ICMS60",
        linked_keys=linked,
        taker_role=role or ("outros" if taker_tax_id else ""),
    )


def _party(root: ET.Element, role: str) -> str:
    return _text(root, _CTE, f".//{role}/CNPJ") or _text(root, _CTE, f".//{role}/CPF")


def _child_text(node: ET.Element | None, group: str, name: str) -> str:
    if node is None:
        return ""
    if not group:
        for child in node.iter():
            if _local(child.tag) == name and child is not node:
                return (child.text or "").strip()
        return ""
    for child in node.iter():
        if _local(child.tag) != group:
            continue
        for leaf in child.iter():
            if _local(leaf.tag) == name:
                return (leaf.text or "").strip()
    return ""


def _child_num(node: ET.Element | None, group: str, name: str) -> float:
    raw = _child_text(node, group, name)
    try:
        return float(raw) if raw else 0.0
    except ValueError:
        return 0.0
