"""CSV/PDF export of the P7 stock-inventory report (doc 119 §8.C).

Single engine: this use case composes ``GetStockInventoryUseCase`` and
serializes the SAME payload the query returns — no second calculation,
no export-only formula. The mandatory metadata header (competence,
branch, scope, closing date, producer, engine, content hash SHA-256,
generated_by/at and the parity watermark) is stamped at the data owner.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    build_pdf,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .get_stock_inventory_use_case import GetStockInventoryUseCase

EXPORT_PAGE_SIZE = 50000
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PDF = "pdf"
EXPORT_FORMATS = (EXPORT_FORMAT_CSV, EXPORT_FORMAT_PDF)

# Statuses representing a real population — anything else never becomes
# a document (a header-only file could masquerade as zero stock).
EXPORTABLE_STATUSES = frozenset(
    {"available", "incomplete", "no_matching_items"}
)

_SCOPE_LABELS = {
    "all_products": "Todos os produtos",
    "mp_pi_pa": "Somente MP, PI e PA",
}

_ITEM_COLUMNS = (
    "product_code",
    "description",
    "product_type",
    "product_group",
    "unit",
    "warehouse",
    "branch_code",
    "historical_quantity",
    "historical_stock_value",
)

_TYPE_SUMMARY_COLUMNS = (
    "product_type",
    "item_count",
    "total_quantity",
    "total_stock_value",
)

_WAREHOUSE_SUMMARY_COLUMNS = (
    "branch_code",
    "warehouse",
    "item_count",
    "total_quantity",
    "total_stock_value",
)

_HASHED_KEYS = (
    "items",
    "stockTotal",
    "processPhysicalTotal",
    "processAllocatedTotal",
    "processTotal",
    "grandTotal",
    "summariesByType",
    "summariesByWarehouse",
)


class StockInventoryNotExportableError(RuntimeError):
    """Payload status cannot certify a document (e.g. source_missing)."""


class StockInventoryExportTruncatedError(RuntimeError):
    """Item population exceeded the export batch — never certify part."""


# OWASP CSV formula injection: text cells opening with these characters
# are neutralized with a leading apostrophe before reaching Excel.
_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_text(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in _DANGEROUS_PREFIXES:
        return "'" + value
    return value


def export_filename(payload: dict[str, Any], export_format: str = "csv") -> str:
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    scope = payload.get("reportScope") or "all_products"
    return f"p7-inventory-{period}-{branch}-{scope}.{export_format}"


def content_hash(payload: dict[str, Any]) -> str:
    """SHA-256 over the data the document certifies (items + totals +
    summaries) — canonical JSON, stable across key order."""
    material = {key: payload.get(key) for key in _HASHED_KEYS}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ExportStockInventoryUseCase:
    """Runs the shared P7 engine unpaginated and serializes its payload."""

    def __init__(self, get_use_case: GetStockInventoryUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: StockInventoryQueryRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        result = self._get_use_case.execute(
            request, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise StockInventoryNotExportableError(
                f"status={payload.get('status')}"
            )
        total_items = int(
            (payload.get("pagination") or {}).get("total_items") or 0
        )
        if len(payload.get("items") or []) < total_items:
            raise StockInventoryExportTruncatedError(
                f"items={len(payload.get('items') or [])} "
                f"total_items={total_items}"
            )

        if export_format == EXPORT_FORMAT_CSV:
            stream = _build_csv(
                payload,
                generated_by=user_subject,
                warehouse_filter=request.warehouse,
            )
            content_type = "text/csv; charset=utf-8"
        else:
            stream = _build_pdf(
                payload,
                generated_by=user_subject,
                warehouse_filter=request.warehouse,
            )
            content_type = "application/pdf"
        return {
            "stream": stream,
            "content_type": content_type,
            "filename": export_filename(payload, export_format),
            "exported_count": len(payload.get("items") or []),
        }


def _build_csv(
    payload: dict[str, Any],
    *,
    generated_by: str | None,
    warehouse_filter: str | None,
) -> io.BytesIO:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    scope = payload.get("reportScope") or "all_products"
    provenance = payload.get("provenance") or {}
    parity_status = payload.get("parityStatus") or "UNVERIFIED"
    official = bool(payload.get("officialP7"))
    branches_missing = payload.get("branchesMissing") or []

    buffer = io.StringIO()
    write = buffer.write

    write("# RELATORIO P7 — REGISTRO DE INVENTARIO DE ESTOQUE\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# escopo={scope}\n")
    write(f"# escopo_rotulo={_SCOPE_LABELS.get(scope, scope)}\n")
    write(f"# data_fechamento={payload.get('dataAsOf')}\n")
    write(f"# produtor_oficial={provenance.get('officialProducer')}\n")
    write(f"# motor={provenance.get('engine')}\n")
    write(f"# fonte={payload.get('source')}\n")
    write(f"# parity_state={parity_status}\n")
    write(f"# oficial={'true' if official else 'false'}\n")
    write(f"# status={payload.get('status')}\n")
    write(
        "# filiais_disponiveis="
        + ",".join(payload.get("branchesAvailable") or [])
        + "\n"
    )
    write(
        "# filiais_ausentes="
        + (",".join(branches_missing) if branches_missing else "nenhuma")
        + "\n"
    )
    write(f"# armazem_filtro={warehouse_filter or 'todos'}\n")
    write(f"# gerado_por={generated_by or 'desconhecido'}\n")
    write(f"# gerado_em={stamp}\n")
    write(f"# hash_conteudo_sha256={content_hash(payload)}\n")
    if not official:
        write(
            "# AVISO: DOCUMENTO NAO OFICIAL — paridade pendente de "
            "homologacao contra nova emissao MATR460; nao substitui o "
            "relatorio oficial do Protheus.\n"
        )
    if branches_missing:
        write(
            "# AVISO: exportacao parcial — filiais sem snapshot "
            "declaradas acima; ausencia nao equivale a valor zero.\n"
        )
    write("\n")

    writer = csv.DictWriter(
        buffer, fieldnames=list(_ITEM_COLUMNS), extrasaction="ignore"
    )
    writer.writeheader()
    for item in payload.get("items") or []:
        writer.writerow(_item_row(item))
    write("\n")

    write("# TOTALIZADORES\n")
    write(f"# em_estoque={payload.get('stockTotal')}\n")
    write(f"# em_processo_fisico={payload.get('processPhysicalTotal')}\n")
    write(f"# em_processo_alocado={payload.get('processAllocatedTotal')}\n")
    write(f"# em_processo={payload.get('processTotal')}\n")
    write(f"# total_geral={payload.get('grandTotal')}\n")
    write(f"# historico_sb9_total={payload.get('historicalTotal')}\n")
    write("\n")

    write("# RESUMO POR TIPO\n")
    type_writer = csv.DictWriter(
        buffer,
        fieldnames=list(_TYPE_SUMMARY_COLUMNS),
        extrasaction="ignore",
    )
    type_writer.writeheader()
    for row in payload.get("summariesByType") or []:
        type_writer.writerow(_type_summary_row(row))
    write("\n")

    write("# RESUMO POR ARMAZEM\n")
    wh_writer = csv.DictWriter(
        buffer,
        fieldnames=list(_WAREHOUSE_SUMMARY_COLUMNS),
        extrasaction="ignore",
    )
    wh_writer.writeheader()
    for row in payload.get("summariesByWarehouse") or []:
        wh_writer.writerow(_warehouse_summary_row(row))
    write("\n")

    write("# PROVENIENCIA\n")
    for key in (
        "engine",
        "officialProducer",
        "snapshotDate",
        "movementCutoff",
        "opAliveCutoff",
        "processWarehouse",
        "reportScope",
        "openOrdersAllocated",
    ):
        write(f"# {key}={provenance.get(key)}\n")
    for note in payload.get("parityNotes") or []:
        write(f"# parity_note={note}\n")

    output = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return output


def _item_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_code": _safe_text(item.get("productCode")),
        "description": _safe_text(item.get("description")),
        "product_type": _safe_text(item.get("productType")),
        "product_group": _safe_text(item.get("productGroup")),
        "unit": _safe_text(item.get("unit")),
        "warehouse": _safe_text(item.get("warehouse")),
        "branch_code": _safe_text(item.get("branchCode")),
        "historical_quantity": item.get("historicalQuantity"),
        "historical_stock_value": item.get("historicalStockValue"),
    }


def _type_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_type": _safe_text(row.get("productType")),
        "item_count": row.get("itemCount"),
        "total_quantity": row.get("totalQuantity"),
        "total_stock_value": row.get("totalStockValue"),
    }


def _warehouse_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_code": _safe_text(row.get("branchCode")),
        "warehouse": _safe_text(row.get("warehouse")),
        "item_count": row.get("itemCount"),
        "total_quantity": row.get("totalQuantity"),
        "total_stock_value": row.get("totalStockValue"),
    }


_PDF_TOTALS_COLUMNS = (("label", "Medida"), ("value", "Valor (R$)"))

_PDF_TYPE_COLUMNS = (
    ("productType", "Tipo"),
    ("itemCount", "Itens"),
    ("totalQuantity", "Quantidade"),
    ("totalStockValue", "Valor (R$)"),
)
_PDF_TYPE_NUMERIC = frozenset(
    {"itemCount", "totalQuantity", "totalStockValue"}
)

_PDF_WAREHOUSE_COLUMNS = (
    ("branchCode", "Filial"),
    ("warehouse", "Armazém"),
    ("itemCount", "Itens"),
    ("totalQuantity", "Quantidade"),
    ("totalStockValue", "Valor (R$)"),
)

_PDF_ITEM_COLUMNS = (
    ("productCode", "Produto"),
    ("description", "Descrição"),
    ("productType", "Tipo"),
    ("unit", "UM"),
    ("warehouse", "Armazém"),
    ("branchCode", "Filial"),
    ("historicalQuantity", "Quantidade"),
    ("historicalStockValue", "Valor (R$)"),
)
_PDF_ITEM_NUMERIC = frozenset(
    {"historicalQuantity", "historicalStockValue"}
)


def _dec_sum(rows: list[dict[str, Any]], key: str) -> Decimal:
    total = Decimal("0")
    for row in rows:
        try:
            total += Decimal(str(row.get(key) or "0"))
        except (InvalidOperation, ValueError):
            continue
    return total


def _build_pdf(
    payload: dict[str, Any],
    *,
    generated_by: str | None,
    warehouse_filter: str | None,
) -> io.BytesIO:
    totals_rows = [
        {"label": "EM ESTOQUE", "value": payload.get("stockTotal")},
        {
            "label": "EM PROCESSO — FÍSICO (LOC. PROCESSO)",
            "value": payload.get("processPhysicalTotal"),
        },
        {
            "label": "EM PROCESSO — ALOCADO (OP)",
            "value": payload.get("processAllocatedTotal"),
        },
        {"label": "EM PROCESSO — TOTAL", "value": payload.get("processTotal")},
        {
            "label": "HISTÓRICO SB9 (REFERÊNCIA)",
            "value": payload.get("historicalTotal"),
        },
        {"label": "TOTAL GERAL", "value": payload.get("grandTotal")},
    ]
    sections = [
        ReportTableSection(
            title="Totais do fechamento",
            columns=list(_PDF_TOTALS_COLUMNS),
            rows=totals_rows,
            align_right_keys=frozenset({"value"}),
            money_keys=frozenset({"value"}),
            note=(
                "«Histórico SB9 (referência)» é a posição gravada no "
                "fechamento do período; «Em estoque» e «Em processo» "
                "compõem o total calculado pelo motor P7 — grandezas "
                "distintas, não um mesmo saldo."
            ),
            keep_together=True,
        ),
        ReportTableSection(
            title="Resumo por tipo de produto",
            columns=list(_PDF_TYPE_COLUMNS),
            rows=[
                {key: row.get(key) for key, _ in _PDF_TYPE_COLUMNS}
                for row in payload.get("summariesByType") or []
            ],
            align_right_keys=_PDF_TYPE_NUMERIC,
            money_keys=frozenset({"totalStockValue"}),
            quantity_keys=frozenset({"totalQuantity"}),
        ),
        ReportTableSection(
            title="Resumo por armazém",
            columns=list(_PDF_WAREHOUSE_COLUMNS),
            rows=[
                {key: row.get(key) for key, _ in _PDF_WAREHOUSE_COLUMNS}
                for row in payload.get("summariesByWarehouse") or []
            ],
            totals_row={
                "branchCode": "TOTAL",
                "warehouse": "",
                "itemCount": sum(
                    int(row.get("itemCount") or 0)
                    for row in payload.get("summariesByWarehouse") or []
                ),
                "totalQuantity": str(
                    _dec_sum(
                        payload.get("summariesByWarehouse") or [],
                        "totalQuantity",
                    )
                ),
                "totalStockValue": str(
                    _dec_sum(
                        payload.get("summariesByWarehouse") or [],
                        "totalStockValue",
                    )
                ),
            },
            align_right_keys=_PDF_TYPE_NUMERIC,
            money_keys=frozenset({"totalStockValue"}),
            quantity_keys=frozenset({"totalQuantity"}),
        ),
        ReportTableSection(
            title="Itens do inventário",
            columns=list(_PDF_ITEM_COLUMNS),
            rows=[
                {key: item.get(key) for key, _ in _PDF_ITEM_COLUMNS}
                for item in payload.get("items") or []
            ],
            align_right_keys=_PDF_ITEM_NUMERIC,
            money_keys=frozenset({"historicalStockValue"}),
            quantity_keys=frozenset({"historicalQuantity"}),
        ),
    ]
    return build_pdf(
        title="P7 — REGISTRO DE INVENTÁRIO DE ESTOQUE",
        payload=payload,
        hashed_keys=_HASHED_KEYS,
        sections=sections,
        generated_by=generated_by,
        extra_metadata=(
            [("Armazém", warehouse_filter)] if warehouse_filter else None
        ),
    )
