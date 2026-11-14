"""Regras da skill sobre objetos já lidos. D11 permanece desligado por padrão.

A paridade compara título, campo, severidade e valores com a skill. O identificador
estável fica ao lado, para a ocorrência da plataforma.
"""

from __future__ import annotations

from datetime import timedelta

from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    AuditResult,
    Occurrence,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
    UnmatchedDocument,
    XmlDocument,
    XmlItem,
)

_INSUMO = {"101", "102", "401", "403", "151", "152", "122", "124", "125", "126"}
_NATURE = {
    "consumo": {"556", "407", "653"},
    "ativo": {"551", "406"},
    "insumo/revenda": {"101", "102", "401", "403", "122", "124", "125", "126"},
}


def audit(
    *,
    branch: str,
    company_tax_id: str,
    company_state: str,
    headers: list[ProtheusHeader],
    items: list[ProtheusItem],
    tes_records: list[TesRecord],
    invoices: dict[str, XmlDocument],
    ctes: dict[str, XmlDocument],
    config: AuditConfig | None = None,
) -> AuditResult:
    settings = config or AuditConfig()
    result = AuditResult()
    tes = {record.code: record for record in tes_records}
    branch_headers = [row for row in headers if row.branch == branch]
    branch_items = [row for row in items if row.branch == branch]
    by_key = {row.access_key: row for row in branch_headers if row.access_key}

    for header in branch_headers:
        if _model(header.access_key) != "55":
            continue
        invoice = invoices.get(header.access_key)
        if invoice is None or invoice.cancelled:
            continue
        _header_rules(result, header, invoice, settings)
        _item_rules(
            result,
            header,
            [row for row in branch_items if _same_document(row, header)],
            invoice,
            tes,
            settings,
        )

    _cte_rules(result, branch_headers, branch_items, ctes, invoices, tes, company_tax_id, company_state, settings)
    _unmatched(result, branch_headers, invoices, ctes, company_tax_id, settings)
    return result


def _header_rules(result: AuditResult, header: ProtheusHeader, invoice: XmlDocument, settings: AuditConfig) -> None:
    if abs(header.gross_amount - invoice.total_amount) > settings.tolerance:
        _add(
            result, header, "", "header.total_mismatch", "Valor total da nota diverge", "Alta",
            "Vlr Total", header.gross_amount, invoice.total_amount, header.access_key,
        )
    if abs(header.goods_amount - invoice.goods_amount) > settings.tolerance:
        _add(
            result, header, "", "header.total_mismatch", "Valor das mercadorias diverge", "Alta",
            "Vlr Mercadorias", header.goods_amount, invoice.goods_amount, header.access_key,
        )


def _item_rules(
    result: AuditResult,
    header: ProtheusHeader,
    rows: list[ProtheusItem],
    invoice: XmlDocument,
    tes: dict[str, TesRecord],
    settings: AuditConfig,
) -> None:
    xml_items = sorted(invoice.items, key=lambda item: item.number)
    if len(xml_items) != len(rows):
        return
    ordered = sorted(rows, key=lambda row: _item_number(row.item))
    for row, xml_item in zip(ordered, xml_items, strict=True):
        _one_item(result, header, row, xml_item, tes, settings)


def _one_item(
    result: AuditResult,
    header: ProtheusHeader,
    row: ProtheusItem,
    xml_item: XmlItem,
    tes: dict[str, TesRecord],
    settings: AuditConfig,
) -> None:
    record = tes.get(row.tes)
    credits = _credits_icms(record)
    reference = xml_item.icms_amount
    if xml_item.origin and row.tax_situation and row.tax_situation[0] != xml_item.origin:
        _add(
            result, header, row.item, "item.origin_mismatch", "Origem da mercadoria divergente", "Média",
            "CST (origem)", row.tax_situation, f"{xml_item.origin}{xml_item.cst or xml_item.csosn}",
            header.access_key,
        )
    if xml_item.cst and row.tax_situation[-2:] != xml_item.cst:
        if row.tax_situation[-2:] == "90" and (row.icms_amount <= settings.tolerance or credits is False):
            result.suppress("suppressed.cst_090")
        elif credits is not False:
            _add(
                result, header, row.item, "item.cst_mismatch", "CST diverge do documento", "Média",
                "CST", row.tax_situation, f"{xml_item.origin}{xml_item.cst}", header.access_key,
            )
    suffix = row.cfop[1:] if len(row.cfop) > 1 else ""
    no_credit = credits is False
    if no_credit and suffix in _INSUMO and reference > settings.tolerance and xml_item.cst:
        _add(
            result, header, row.item, "item.highlighted_icms_not_credited",
            "ICMS destacado não creditado em insumo/revenda (TES sem crédito)", "Média",
            "ICMS", 0.0, reference, header.access_key,
        )
    elif abs(row.icms_amount - reference) <= settings.tolerance:
        return
    elif row.icms_amount > settings.tolerance and reference <= settings.tolerance and credits is not False:
        _add(
            result, header, row.item, "item.icms_above_xml", "ICMS calculado sem destaque no XML",
            "Depende da TES", "ICMS", row.icms_amount, reference, header.access_key,
        )


def _cte_rules(
    result: AuditResult,
    headers: list[ProtheusHeader],
    items: list[ProtheusItem],
    ctes: dict[str, XmlDocument],
    invoices: dict[str, XmlDocument],
    tes: dict[str, TesRecord],
    company_tax_id: str,
    company_state: str,
    settings: AuditConfig,
) -> None:
    del invoices, company_tax_id
    for header in headers:
        if _model(header.access_key) not in {"57", "67"}:
            continue
        document = ctes.get(header.access_key)
        if document is None:
            continue
        if abs(header.gross_amount - document.service_amount) > settings.tolerance:
            _add(
                result, header, "", "cte.service_amount_mismatch", "CT-e: valor da prestação diverge", "Alta",
                "Vlr Total", header.gross_amount, document.service_amount, header.access_key,
            )
        rows = [row for row in items if _same_document(row, header)]
        expected = ("1" if document.origin_state == company_state else "2") + settings.freight_cfop_suffix
        if rows and any(row.cfop != expected for row in rows):
            _add(
                result, header, rows[0].item, "cte.cfop_mismatch", "CT-e: CFOP divergente", "Média",
                "CFOP", ", ".join(sorted({row.cfop for row in rows})), expected, header.access_key,
            )
        credits = any(_credits_icms(tes.get(row.tes)) is True for row in rows)
        if credits and document.icms_amount <= settings.tolerance and _freight_without_right(document, rows):
            _add(
                result, header, "", "cte.credit_without_right", "CT-e: crédito de ICMS em frete sem direito",
                "Alta", "ICMS", header.icms_amount, 0.0, header.access_key,
            )


def _unmatched(
    result: AuditResult,
    headers: list[ProtheusHeader],
    invoices: dict[str, XmlDocument],
    ctes: dict[str, XmlDocument],
    company_tax_id: str,
    settings: AuditConfig,
) -> None:
    booked = {row.access_key for row in headers if row.access_key}
    issued = [doc.issued_at for doc in invoices.values() if doc.issued_at is not None]
    latest = max(issued) if issued else None
    grace = latest - timedelta(days=settings.unmatched_grace_days) if latest else None
    for document in invoices.values():
        if document.access_key in booked or document.cancelled:
            continue
        if document.issuer_tax_id == company_tax_id and document.direction == "Saída":
            continue
        reason = "Recebida de terceiro e ainda não escriturada na SF1."
        if document.issued_at is not None and grace is not None and document.issued_at >= grace:
            reason += " Emissão recente: pode estar em trânsito."
        result.unmatched.append(
            UnmatchedDocument("xml", str(document.number), "Média", reason, document.access_key, "SPED")
        )
    xml_span = [doc.issued_at for doc in list(invoices.values()) + list(ctes.values()) if doc.issued_at]
    earliest = min(xml_span) if xml_span else None
    for header in headers:
        model = _model(header.access_key)
        pool = invoices if model == "55" else ctes if model in {"57", "67"} else None
        if pool is None or header.access_key in pool:
            continue
        if earliest is not None and header.issue_date is not None and header.issue_date < earliest.date():
            reason = "Emitida antes do período do download de XML."
            severity = "Info"
        else:
            reason = "Emitida dentro do período, mas o XML não veio no download. Baixar e conferir."
            severity = "Média"
        result.unmatched.append(
            UnmatchedDocument("protheus", header.number, severity, reason, header.access_key, header.species)
        )


def _freight_without_right(document: XmlDocument, rows: list[ProtheusItem]) -> bool:
    if document.simples_national or document.icms_amount <= 0.05:
        return True
    natures = set()
    for row in rows:
        suffix = row.cfop[1:] if len(row.cfop) > 1 else ""
        for name, codes in _NATURE.items():
            if suffix in codes:
                natures.add(name)
    return bool(natures) and natures <= {"consumo", "ativo"}


def _credits_icms(record: TesRecord | None) -> bool | None:
    if record is None:
        return None
    if record.calculates_icms == "Sim" and record.credits_icms == "Sim" and record.icms_book != "Tributado":
        return None
    if record.calculates_icms == "Sim" and record.credits_icms == "Nao" and record.icms_book == "Tributado":
        return None
    return record.credits_icms == "Sim"


def _same_document(item: ProtheusItem, header: ProtheusHeader) -> bool:
    return (
        item.number == header.number
        and _series(item.series) == _series(header.series)
        and item.supplier_code == header.supplier_code
        and item.supplier_store == header.supplier_store
    )


def _series(value: str) -> str:
    return (value or "").strip().upper().lstrip("0") or "0"


def _model(access_key: str) -> str:
    return access_key[20:22] if len(access_key) == 44 else ""


def _item_number(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def _add(
    result: AuditResult,
    header: ProtheusHeader,
    item: str,
    rule_id: str,
    title: str,
    severity: str,
    field: str,
    protheus_value,
    xml_value,
    access_key: str,
) -> None:
    result.occurrences.append(
        Occurrence(
            rule_id=rule_id,
            title=title,
            severity=severity,
            document_number=header.number,
            item=item,
            field=field,
            protheus_value=_render(protheus_value),
            xml_value=_render(xml_value),
            access_key=access_key,
        )
    )


def _render(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{float(value):.2f}"
    return str(value).strip()
