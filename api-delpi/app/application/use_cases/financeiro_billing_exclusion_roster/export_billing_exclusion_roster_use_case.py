"""CSV/PDF export of the R11 billing-exclusion roster (doc 126 §17).

Single engine: this use case composes ``ListBillingExclusionRosterUseCase``
and serializes the SAME payload — the mandatory metadata header
(competence, branch, view, selection criteria, producer, engine,
SHA-256 content hash, generated_by/at and the parity watermark) is
stamped at the data owner. The exported document is operational and
investigative — never an official R11 emission — and the
out-of-criteria population never blends into the roster totals.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any

from app.application.dto.financeiro_billing_exclusion_roster.billing_exclusion_roster_request import (
    BillingExclusionRosterRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    build_pdf,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .list_billing_exclusion_roster_use_case import (
    ListBillingExclusionRosterUseCase,
)

EXPORT_PAGE_SIZE = 50000
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PDF = "pdf"
EXPORT_FORMATS = (EXPORT_FORMAT_CSV, EXPORT_FORMAT_PDF)

EXPORTABLE_STATUSES = frozenset({"available", "no_matching_items"})

_ITEM_COLUMNS = (
    "branch_code",
    "document",
    "series",
    "item",
    "product_code",
    "product_description",
    "product_type",
    "product_group",
    "tes",
    "tes_description",
    "cf",
    "customer_code",
    "customer_store",
    "customer_name",
    "account_code",
    "warehouse",
    "order_number",
    "issue_date",
    "quantity",
    "unit_price",
    "total_value",
    "stock_cost",
    "tes_stock_movement",
    "tes_duplicate_flag",
    "document_item_count",
    "has_stock_sibling_item",
    "selection_status",
    "cost_status",
    "findings",
)

_FINDING_COLUMNS = (
    "finding_id",
    "rule_id",
    "status",
    "line_id",
    "document",
    "series",
    "item",
    "product_code",
    "tes",
    "explanation",
    "erp_guidance",
)

_HASHED_KEYS = ("items", "findings", "summary")


class BillingExclusionRosterNotExportableError(RuntimeError):
    """Payload status cannot certify a document."""


class BillingExclusionRosterExportTruncatedError(RuntimeError):
    """Population exceeded the export batch — never certify part of it."""


_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_text(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in _DANGEROUS_PREFIXES:
        return "'" + value
    return value


def export_filename(payload: dict[str, Any], export_format: str = "csv") -> str:
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    view = payload.get("view") or "candidates"
    return f"billing-exclusion-roster-{period}-{branch}-{view}.{export_format}"


def content_hash(payload: dict[str, Any]) -> str:
    material = {key: payload.get(key) for key in _HASHED_KEYS}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ExportBillingExclusionRosterUseCase:
    """Runs the shared R11 engine unpaginated and serializes it."""

    def __init__(self, get_use_case: ListBillingExclusionRosterUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: BillingExclusionRosterRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        result = self._get_use_case.execute(
            request, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise BillingExclusionRosterNotExportableError(
                f"status={payload.get('status')}"
            )
        total_items = int(
            (payload.get("pagination") or {}).get("total_items") or 0
        )
        if len(payload.get("items") or []) < total_items:
            raise BillingExclusionRosterExportTruncatedError(
                f"items={len(payload.get('items') or [])} "
                f"total_items={total_items}"
            )
        if payload.get("findingsTruncated"):
            raise BillingExclusionRosterExportTruncatedError(
                "findings truncated"
            )

        if export_format == EXPORT_FORMAT_CSV:
            stream = _build_csv(payload, generated_by=user_subject)
            content_type = "text/csv; charset=utf-8"
        else:
            stream = _build_pdf(payload, generated_by=user_subject)
            content_type = "application/pdf"
        return {
            "stream": stream,
            "content_type": content_type,
            "filename": export_filename(payload, export_format),
            "exported_count": len(payload.get("items") or []),
        }


def _build_csv(
    payload: dict[str, Any], *, generated_by: str | None
) -> io.BytesIO:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provenance = payload.get("provenance") or {}
    selection = payload.get("selection") or {}
    criteria = selection.get("observedCriteria") or {}
    summary = payload.get("summary") or {}

    buffer = io.StringIO()
    write = buffer.write
    write("# RELATORIO R11 — NOTAS FISCAIS A DESCONSIDERAR\n")
    write("# CARATER: lista investigativa de conferencia — nenhuma nota\n")
    write("# e excluida automaticamente de CPV, faturamento ou DRE.\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# visao={payload.get('view')}\n")
    write(f"# eixo_competencia={selection.get('axis')}\n")
    write(f"# grao={selection.get('grain')}\n")
    write(
        "# criterio_observado=grupo:"
        + str(criteria.get("productGroup"))
        + " + tes:"
        + str(criteria.get("tes"))
        + "\n"
    )
    write(f"# oficialidade_predicado={selection.get('predicateOfficiality')}\n")
    write(f"# apuracao_afetada={selection.get('affectedCalculation')}\n")
    write(f"# produtor_oficial={provenance.get('officialProducer')}\n")
    write(f"# motor={provenance.get('engine')}\n")
    write(f"# fonte={payload.get('source')}\n")
    write(f"# status={payload.get('status')}\n")
    write(f"# parity_state={payload.get('parityStatus')}\n")
    write(f"# gerado_por={generated_by or 'desconhecido'}\n")
    write(f"# gerado_em={stamp}\n")
    write(f"# hash_conteudo_sha256={content_hash(payload)}\n")
    write(
        "# AVISO: DOCUMENTO NAO OFICIAL — paridade pendente de "
        "homologacao humana; achados sao POSSIBLE_DIVERGENCE, nunca "
        "erro confirmado; correcao e atividade externa no Protheus.\n\n"
    )

    writer = csv.DictWriter(
        buffer, fieldnames=list(_ITEM_COLUMNS), extrasaction="ignore"
    )
    writer.writeheader()
    for item in payload.get("items") or []:
        writer.writerow(_item_row(item))
    write("\n")

    write("# TOTALIZADORES DA POPULACAO CONSULTADA\n")
    for key, value in summary.items():
        if isinstance(value, list):
            continue
        write(f"# {key}={value}\n")
    write("\n")

    findings = payload.get("findings") or []
    if findings:
        write("# POSSIVEIS DIVERGENCIAS\n")
        finding_writer = csv.DictWriter(
            buffer,
            fieldnames=list(_FINDING_COLUMNS),
            extrasaction="ignore",
        )
        finding_writer.writeheader()
        for finding in findings:
            src = finding.get("sourceRecord") or {}
            finding_writer.writerow(
                {
                    "finding_id": finding.get("findingId"),
                    "rule_id": finding.get("ruleId"),
                    "status": finding.get("status"),
                    "line_id": finding.get("lineId"),
                    "document": _safe_text(src.get("document")),
                    "series": _safe_text(src.get("series")),
                    "item": _safe_text(src.get("item")),
                    "product_code": _safe_text(src.get("productCode")),
                    "tes": _safe_text(src.get("tes")),
                    "explanation": _safe_text(
                        finding.get("findingExplanation")
                    ),
                    "erp_guidance": _safe_text(
                        finding.get("erpReviewGuidance")
                    ),
                }
            )
        write("\n")

    write("# PROVENIENCIA\n")
    for key, value in provenance.items():
        write(f"# {key}={value}\n")
    for note in payload.get("parityNotes") or []:
        write(f"# parity_note={note}\n")

    output = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return output


def _item_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_code": _safe_text(item.get("branchCode")),
        "document": _safe_text(item.get("document")),
        "series": _safe_text(item.get("series")),
        "item": _safe_text(item.get("item")),
        "product_code": _safe_text(item.get("productCode")),
        "product_description": _safe_text(item.get("productDescription")),
        "product_type": _safe_text(item.get("productType")),
        "product_group": _safe_text(item.get("productGroup")),
        "tes": _safe_text(item.get("tes")),
        "tes_description": _safe_text(item.get("tesDescription")),
        "cf": _safe_text(item.get("cf")),
        "customer_code": _safe_text(item.get("customerCode")),
        "customer_store": _safe_text(item.get("customerStore")),
        "customer_name": _safe_text(item.get("customerName")),
        "account_code": _safe_text(item.get("accountCode")),
        "warehouse": _safe_text(item.get("warehouse")),
        "order_number": _safe_text(item.get("orderNumber")),
        "issue_date": item.get("issueDate"),
        "quantity": item.get("quantity"),
        "unit_price": item.get("unitPrice"),
        "total_value": item.get("totalValue"),
        "stock_cost": item.get("stockCost"),
        "tes_stock_movement": item.get("tesStockMovement"),
        "tes_duplicate_flag": item.get("tesDuplicateFlag"),
        "document_item_count": item.get("documentItemCount"),
        "has_stock_sibling_item": item.get("hasStockSiblingItem"),
        "selection_status": item.get("selectionStatus"),
        "cost_status": item.get("costStatus"),
        "findings": "|".join(item.get("findings") or []),
    }


_PDF_TOTALS_COLUMNS = (("label", "Medida"), ("value", "Valor"))

_PDF_ITEM_COLUMNS = (
    ("issueDate", "Emissão"),
    ("document", "Documento"),
    ("item", "Item"),
    ("productCode", "Produto"),
    ("productGroup", "Grupo"),
    ("tes", "TES"),
    ("cf", "CFOP"),
    ("quantity", "Qtd."),
    ("totalValue", "Valor (R$)"),
    ("stockCost", "Custo Est. (R$)"),
    ("hasStockSiblingItem", "Item-irmão Est."),
    ("selectionStatus", "Situação"),
)
_PDF_ITEM_NUMERIC = frozenset({"quantity", "totalValue", "stockCost"})
_PDF_ITEM_MONEY = frozenset({"totalValue", "stockCost"})


def _build_pdf(
    payload: dict[str, Any], *, generated_by: str | None
) -> io.BytesIO:
    summary = payload.get("summary") or {}
    totals_rows = [
        {"label": "VISÃO", "value": payload.get("view")},
        {"label": "LINHAS", "value": summary.get("lineCount")},
        {"label": "VALOR TOTAL (R$)", "value": summary.get("totalValue")},
        {"label": "DOCUMENTOS", "value": summary.get("documentCount")},
        {
            "label": "CANDIDATAS (CRITÉRIO HISTÓRICO)",
            "value": summary.get("candidateLineCount"),
        },
        {
            "label": "RELACIONADAS FORA DO CRITÉRIO",
            "value": summary.get("outOfCriteriaLineCount"),
        },
        {
            "label": "DOCS SEM ITEM-IRMÃO DE ESTOQUE",
            "value": summary.get("missingStockSiblingDocumentCount"),
        },
        {
            "label": "POSSÍVEIS DIVERGÊNCIAS",
            "value": summary.get("findingCount"),
        },
    ]
    sections = [
        ReportTableSection(
            title="Totais da população consultada",
            columns=list(_PDF_TOTALS_COLUMNS),
            rows=totals_rows,
            align_right_keys=frozenset({"value"}),
            keep_together=True,
        ),
        ReportTableSection(
            title="Notas fiscais",
            columns=list(_PDF_ITEM_COLUMNS),
            rows=[
                {
                    **{key: item.get(key) for key, _ in _PDF_ITEM_COLUMNS},
                    "hasStockSiblingItem": (
                        "sim" if item.get("hasStockSiblingItem") else "não"
                    ),
                }
                for item in payload.get("items") or []
            ],
            align_right_keys=_PDF_ITEM_NUMERIC,
            money_keys=_PDF_ITEM_MONEY,
            quantity_keys=frozenset({"quantity"}),
        ),
    ]
    return build_pdf(
        title="R11 — NOTAS FISCAIS A DESCONSIDERAR",
        payload=payload,
        hashed_keys=_HASHED_KEYS,
        sections=sections,
        generated_by=generated_by,
        extra_metadata=[("Visão", payload.get("view") or "candidates")],
    )
