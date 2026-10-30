"""CSV/PDF export of the R10 cost-center-expenses report (doc 126 §17).

Single engine: this use case composes ``ListCostCenterExpensesUseCase``
and serializes the SAME payload — the mandatory metadata header
(competence, branch, UNIVERSE, selection criteria, producer, engine,
SHA-256 content hash, generated_by/at and the parity watermark) is
stamped at the data owner. The exported document is operational — never
an official R10 emission — and the investigation universe never blends
into the calculation totals.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any

from app.application.dto.financeiro_cost_center_expenses.cost_center_expenses_request import (
    CostCenterExpensesRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    build_pdf,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .list_cost_center_expenses_use_case import (
    ListCostCenterExpensesUseCase,
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
    "sequence",
    "product_code",
    "product_description",
    "product_type",
    "product_group",
    "cost_center",
    "cost_center_description",
    "cost_center_catalog_status",
    "account_code",
    "tes",
    "cf",
    "supplier_code",
    "supplier_store",
    "supplier_name",
    "warehouse",
    "order_number",
    "entry_date",
    "issue_date",
    "quantity",
    "unit_value",
    "total_value",
    "universe",
    "calculation_exclusion",
    "cost_class",
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
    "cost_center",
    "explanation",
    "erp_guidance",
)

_HASHED_KEYS = ("items", "findings", "summary")


class CostCenterExpensesNotExportableError(RuntimeError):
    """Payload status cannot certify a document."""


class CostCenterExpensesExportTruncatedError(RuntimeError):
    """Population exceeded the export batch — never certify part of it."""


_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_text(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in _DANGEROUS_PREFIXES:
        return "'" + value
    return value


def export_filename(payload: dict[str, Any], export_format: str = "csv") -> str:
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    universe = payload.get("universe") or "calculation"
    return f"cost-center-expenses-{period}-{branch}-{universe}.{export_format}"


def content_hash(payload: dict[str, Any]) -> str:
    material = {key: payload.get(key) for key in _HASHED_KEYS}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ExportCostCenterExpensesUseCase:
    """Runs the shared R10 engine unpaginated and serializes it."""

    def __init__(self, get_use_case: ListCostCenterExpensesUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: CostCenterExpensesRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        result = self._get_use_case.execute(
            request, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise CostCenterExpensesNotExportableError(
                f"status={payload.get('status')}"
            )
        total_items = int(
            (payload.get("pagination") or {}).get("total_items") or 0
        )
        if len(payload.get("items") or []) < total_items:
            raise CostCenterExpensesExportTruncatedError(
                f"items={len(payload.get('items') or [])} "
                f"total_items={total_items}"
            )
        if payload.get("findingsTruncated"):
            raise CostCenterExpensesExportTruncatedError(
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
    summary = payload.get("summary") or {}

    buffer = io.StringIO()
    write = buffer.write
    write("# RELATORIO R10 — DESPESAS POR CENTRO DE CUSTO\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# universo={payload.get('universe')}\n")
    write(f"# eixo_competencia={selection.get('axis')}\n")
    write(f"# grao={selection.get('grain')}\n")
    write(
        "# tes_excluidos="
        + ",".join(selection.get("excludedTes") or [])
        + "\n"
    )
    write(f"# exclui_mp={selection.get('excludeMp')}\n")
    write(f"# exclui_beneficios={selection.get('excludeBenefits')}\n")
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
        "erro confirmado; correcao e atividade externa no Protheus.\n"
    )
    write(
        "# AVISO: totalizadores referem-se SOMENTE ao universo "
        f"'{payload.get('universe')}' — apuracao e investigacao nunca "
        "sao somados.\n\n"
    )

    writer = csv.DictWriter(
        buffer, fieldnames=list(_ITEM_COLUMNS), extrasaction="ignore"
    )
    writer.writeheader()
    for item in payload.get("items") or []:
        writer.writerow(_item_row(item))
    write("\n")

    write("# TOTALIZADORES DO UNIVERSO\n")
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
                    "cost_center": _safe_text(
                        src.get("costCenterCode")
                    ),
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
        "sequence": _safe_text(item.get("sequence")),
        "product_code": _safe_text(item.get("productCode")),
        "product_description": _safe_text(item.get("productDescription")),
        "product_type": _safe_text(item.get("productType")),
        "product_group": _safe_text(item.get("productGroup")),
        "cost_center": _safe_text(item.get("costCenter")),
        "cost_center_description": _safe_text(
            item.get("costCenterDescription")
        ),
        "cost_center_catalog_status": item.get("costCenterCatalogStatus"),
        "account_code": _safe_text(item.get("accountCode")),
        "tes": _safe_text(item.get("tes")),
        "cf": _safe_text(item.get("cf")),
        "supplier_code": _safe_text(item.get("supplierCode")),
        "supplier_store": _safe_text(item.get("supplierStore")),
        "supplier_name": _safe_text(item.get("supplierName")),
        "warehouse": _safe_text(item.get("warehouse")),
        "order_number": _safe_text(item.get("orderNumber")),
        "entry_date": item.get("entryDate"),
        "issue_date": item.get("issueDate"),
        "quantity": item.get("quantity"),
        "unit_value": item.get("unitValue"),
        "total_value": item.get("totalValue"),
        "universe": item.get("universe"),
        "calculation_exclusion": item.get("calculationExclusion"),
        "cost_class": item.get("costClass"),
        "findings": "|".join(item.get("findings") or []),
    }


_PDF_TOTALS_COLUMNS = (("label", "Medida"), ("value", "Valor"))

_PDF_ITEM_COLUMNS = (
    ("entryDate", "Data Digitação"),
    ("document", "Documento"),
    ("item", "Item"),
    ("productCode", "Produto"),
    ("productType", "Tipo"),
    ("costCenter", "Centro Custo"),
    ("tes", "TES"),
    ("quantity", "Qtd."),
    ("totalValue", "Valor (R$)"),
    ("calculationExclusion", "Fora da Apuração"),
    ("findings", "Alertas"),
)
_PDF_ITEM_NUMERIC = frozenset({"quantity", "totalValue"})
_PDF_ITEM_MONEY = frozenset({"totalValue"})


def _build_pdf(
    payload: dict[str, Any], *, generated_by: str | None
) -> io.BytesIO:
    summary = payload.get("summary") or {}
    universe = payload.get("universe") or "calculation"
    totals_rows = [
        {"label": "UNIVERSO", "value": universe},
        {"label": "LINHAS", "value": summary.get("lineCount")},
        {"label": "VALOR TOTAL (R$)", "value": summary.get("totalValue")},
        {"label": "DOCUMENTOS", "value": summary.get("documentCount")},
        {
            "label": "CENTROS DE CUSTO",
            "value": summary.get("costCenterCount"),
        },
        {
            "label": "POSSÍVEIS DIVERGÊNCIAS",
            "value": summary.get("findingCount"),
        },
    ]
    sections = [
        ReportTableSection(
            title="Totais do universo",
            columns=list(_PDF_TOTALS_COLUMNS),
            rows=totals_rows,
            align_right_keys=frozenset({"value"}),
            keep_together=True,
        ),
        ReportTableSection(
            title="Lançamentos",
            columns=list(_PDF_ITEM_COLUMNS),
            rows=[
                {
                    **{key: item.get(key) for key, _ in _PDF_ITEM_COLUMNS},
                    "findings": "|".join(item.get("findings") or []),
                }
                for item in payload.get("items") or []
            ],
            align_right_keys=_PDF_ITEM_NUMERIC,
            money_keys=_PDF_ITEM_MONEY,
            quantity_keys=frozenset({"quantity"}),
        ),
    ]
    return build_pdf(
        title="R10 — DESPESAS POR CENTRO DE CUSTO",
        payload=payload,
        hashed_keys=_HASHED_KEYS,
        sections=sections,
        generated_by=generated_by,
        extra_metadata=[("Universo", universe)],
    )
