"""CSV/PDF export of the R06/R07 kardex reports (doc 122 §12, D-O2).

Single engine: this use case composes ``GetStockKardexUseCase`` and
serializes the SAME payload — the mandatory metadata header
(competence, branch, warehouse, closing date, producer, engine, SHA-256
content hash, generated_by/at and the parity watermark) is stamped at
the data owner. The exported document is operational — never an
official MATR910 emission.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    build_pdf,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .get_stock_kardex_use_case import GetStockKardexUseCase

EXPORT_PAGE_SIZE = 50000
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PDF = "pdf"
EXPORT_FORMATS = (EXPORT_FORMAT_CSV, EXPORT_FORMAT_PDF)

EXPORTABLE_STATUSES = frozenset(
    {"available", "incomplete", "no_matching_items"}
)

_MOVEMENT_COLUMNS = (
    "source_table",
    "branch_code",
    "warehouse",
    "product_code",
    "description",
    "document",
    "series",
    "movement_date",
    "sequence",
    "tm",
    "cf",
    "reference",
    "movement_kind",
    "is_return",
    "document_type",
    "entry_quantity",
    "entry_value",
    "output_quantity",
    "output_value",
    "unit_cost",
    "cost_as_of_source",
    "running_quantity",
    "running_value",
)

_BLOCK_COLUMNS = (
    "product_code",
    "description",
    "product_type",
    "unit",
    "branch_code",
    "warehouse",
    "opening_quantity",
    "opening_value",
    "entry_quantity_total",
    "entry_value_total",
    "output_quantity_total",
    "output_value_total",
    "closing_quantity",
    "closing_value",
    "movement_count",
    "has_opening_snapshot",
)

_HASHED_KEYS = ("items", "blocks", "totals")


class StockKardexNotExportableError(RuntimeError):
    """Payload status cannot certify a document (e.g. source_missing)."""


class StockKardexExportTruncatedError(RuntimeError):
    """Movement population exceeded the export batch — never certify
    part of it."""


_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_text(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in _DANGEROUS_PREFIXES:
        return "'" + value
    return value


def export_filename(payload: dict[str, Any], export_format: str = "csv") -> str:
    report = payload.get("report") or "stock-kardex"
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    return f"{report}-{period}-{branch}.{export_format}"


def content_hash(payload: dict[str, Any]) -> str:
    material = {key: payload.get(key) for key in _HASHED_KEYS}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ExportStockKardexUseCase:
    """Runs the shared kardex engine unpaginated and serializes it."""

    def __init__(self, get_use_case: GetStockKardexUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: StockKardexQueryRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        result = self._get_use_case.execute(
            request, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise StockKardexNotExportableError(
                f"status={payload.get('status')}"
            )
        total_items = int(
            (payload.get("pagination") or {}).get("total_items") or 0
        )
        if len(payload.get("items") or []) < total_items:
            raise StockKardexExportTruncatedError(
                f"items={len(payload.get('items') or [])} "
                f"total_items={total_items}"
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


def _build_csv(payload: dict[str, Any], *, generated_by: str | None) -> io.BytesIO:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provenance = payload.get("provenance") or {}
    parity_status = payload.get("parityStatus") or "UNVERIFIED"
    report = payload.get("report") or "stock-kardex"
    title = (
        "R07 — AJUSTES DE INVENTARIO"
        if report == "inventory-adjustments"
        else "R06 — KARDEX DIARIO / CPV (MATR910)"
    )

    buffer = io.StringIO()
    write = buffer.write
    write(f"# RELATORIO {title}\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# armazem={payload.get('warehouse') or 'todos'}\n")
    write(f"# tipo_documento={payload.get('documentKind')}\n")
    write(f"# produto_filtro={payload.get('productCode') or 'todos'}\n")
    write(f"# data_referencia={payload.get('dataAsOf')}\n")
    write(f"# produtor_oficial={provenance.get('officialProducer')}\n")
    write(f"# motor={provenance.get('engine')}\n")
    write(f"# fonte={payload.get('source')}\n")
    write(f"# convencao_custo={provenance.get('asOfConvention')}\n")
    write(f"# saldo_inicial_fonte={provenance.get('openingBalanceSource')}\n")
    write(f"# snapshot_abertura={provenance.get('snapshotDate')}\n")
    write(f"# parity_state={parity_status}\n")
    write(f"# status={payload.get('status')}\n")
    write(
        "# filiais_disponiveis="
        + ",".join(payload.get("branchesAvailable") or [])
        + "\n"
    )
    missing = payload.get("branchesMissing") or []
    write(
        "# filiais_ausentes="
        + (",".join(missing) if missing else "nenhuma")
        + "\n"
    )
    write(f"# gerado_por={generated_by or 'desconhecido'}\n")
    write(f"# gerado_em={stamp}\n")
    write(f"# hash_conteudo_sha256={content_hash(payload)}\n")
    write(
        "# AVISO: DOCUMENTO NAO OFICIAL — paridade pendente de "
        "homologacao contra nova emissao MATR910; nao substitui o "
        "relatorio oficial do Protheus.\n"
    )
    if missing:
        write(
            "# AVISO: exportacao parcial — filiais sem snapshot "
            "declaradas acima; ausencia nao equivale a valor zero.\n"
        )
    write("\n")

    writer = csv.DictWriter(
        buffer, fieldnames=list(_MOVEMENT_COLUMNS), extrasaction="ignore"
    )
    writer.writeheader()
    for item in payload.get("items") or []:
        writer.writerow(_movement_row(item))
    write("\n")

    totals = payload.get("totals") or {}
    write("# TOTALIZADORES\n")
    for key, value in totals.items():
        write(f"# {key}={value}\n")
    write("\n")

    write("# BLOCOS POR PRODUTO\n")
    block_writer = csv.DictWriter(
        buffer, fieldnames=list(_BLOCK_COLUMNS), extrasaction="ignore"
    )
    block_writer.writeheader()
    for block in payload.get("blocks") or []:
        block_writer.writerow(_block_row(block))
    write("\n")

    write("# PROVENIENCIA\n")
    for key in (
        "engine",
        "officialProducer",
        "snapshotDate",
        "movementWindowStart",
        "movementWindowEnd",
        "documentKind",
        "asOfConvention",
        "costAsOfBoundary",
        "costAsOfTtatMovements",
        "openingBalanceSource",
    ):
        write(f"# {key}={provenance.get(key)}\n")
    for note in payload.get("parityNotes") or []:
        write(f"# parity_note={note}\n")

    output = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return output


def _movement_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_table": _safe_text(item.get("sourceTable")),
        "branch_code": _safe_text(item.get("branchCode")),
        "warehouse": _safe_text(item.get("warehouse")),
        "product_code": _safe_text(item.get("productCode")),
        "description": _safe_text(item.get("description")),
        "document": _safe_text(item.get("document")),
        "series": _safe_text(item.get("series")),
        "movement_date": item.get("movementDate"),
        "sequence": _safe_text(item.get("sequence")),
        "tm": _safe_text(item.get("tm")),
        "cf": _safe_text(item.get("cf")),
        "reference": _safe_text(item.get("reference")),
        "movement_kind": item.get("movementKind"),
        "is_return": item.get("isReturn"),
        "document_type": _safe_text(item.get("documentType")),
        "entry_quantity": item.get("entryQuantity"),
        "entry_value": item.get("entryValue"),
        "output_quantity": item.get("outputQuantity"),
        "output_value": item.get("outputValue"),
        "unit_cost": item.get("unitCost"),
        "cost_as_of_source": item.get("costAsOfSource"),
        "running_quantity": item.get("runningQuantity"),
        "running_value": item.get("runningValue"),
    }


def _block_row(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_code": _safe_text(block.get("productCode")),
        "description": _safe_text(block.get("description")),
        "product_type": _safe_text(block.get("productType")),
        "unit": _safe_text(block.get("unit")),
        "branch_code": _safe_text(block.get("branchCode")),
        "warehouse": _safe_text(block.get("warehouse")),
        "opening_quantity": block.get("openingQuantity"),
        "opening_value": block.get("openingValue"),
        "entry_quantity_total": block.get("entryQuantityTotal"),
        "entry_value_total": block.get("entryValueTotal"),
        "output_quantity_total": block.get("outputQuantityTotal"),
        "output_value_total": block.get("outputValueTotal"),
        "closing_quantity": block.get("closingQuantity"),
        "closing_value": block.get("closingValue"),
        "movement_count": block.get("movementCount"),
        "has_opening_snapshot": block.get("hasOpeningSnapshot"),
    }


_PDF_TOTALS_COLUMNS = (("label", "Medida"), ("value", "Valor"))

_PDF_BLOCK_COLUMNS = (
    ("productCode", "Produto"),
    ("description", "Descrição"),
    ("warehouse", "Armazém"),
    ("branchCode", "Filial"),
    ("openingQuantity", "Qtd. Inicial"),
    ("openingValue", "Valor Inicial (R$)"),
    ("entryQuantityTotal", "Qtd. Entradas"),
    ("entryValueTotal", "Valor Entradas (R$)"),
    ("outputQuantityTotal", "Qtd. Saídas"),
    ("outputValueTotal", "Valor Saídas (R$)"),
    ("closingQuantity", "Qtd. Final"),
    ("closingValue", "Valor Final (R$)"),
)
_PDF_BLOCK_NUMERIC = frozenset(
    {
        "openingQuantity",
        "openingValue",
        "entryQuantityTotal",
        "entryValueTotal",
        "outputQuantityTotal",
        "outputValueTotal",
        "closingQuantity",
        "closingValue",
    }
)
_PDF_BLOCK_MONEY = frozenset(
    {
        "openingValue",
        "entryValueTotal",
        "outputValueTotal",
        "closingValue",
    }
)

_PDF_ITEM_COLUMNS = (
    ("movementDate", "Data"),
    ("sourceTable", "Origem"),
    ("document", "Documento"),
    ("sequence", "Seq."),
    ("productCode", "Produto"),
    ("tm", "TM"),
    ("reference", "Ref."),
    ("movementKind", "Tipo"),
    ("entryQuantity", "Qtd. Entrada"),
    ("entryValue", "Valor Entrada (R$)"),
    ("outputQuantity", "Qtd. Saída"),
    ("outputValue", "Valor Saída (R$)"),
    ("runningQuantity", "Saldo Qtd."),
    ("runningValue", "Saldo Valor (R$)"),
)
_PDF_ITEM_NUMERIC = frozenset(
    {
        "entryQuantity",
        "entryValue",
        "outputQuantity",
        "outputValue",
        "runningQuantity",
        "runningValue",
    }
)
_PDF_ITEM_MONEY = frozenset(
    {"entryValue", "outputValue", "runningValue"}
)


def _dec_sum(rows: list[dict[str, Any]], key: str) -> Decimal:
    total = Decimal("0")
    for row in rows:
        try:
            total += Decimal(str(row.get(key) or "0"))
        except (InvalidOperation, ValueError):
            continue
    return total


def _build_pdf(payload: dict[str, Any], *, generated_by: str | None) -> io.BytesIO:
    report = payload.get("report") or "stock-kardex"
    title = (
        "R07 — AJUSTES DE INVENTÁRIO"
        if report == "inventory-adjustments"
        else "R06 — KARDEX DIÁRIO / CPV (MATR910)"
    )
    totals = payload.get("totals") or {}
    totals_rows = [
        {"label": "MOVIMENTOS", "value": totals.get("movementCount")},
        {"label": "BLOCOS DE PRODUTO", "value": totals.get("blockCount")},
        {"label": "QTD. ENTRADAS", "value": totals.get("entryQuantity")},
        {"label": "VALOR ENTRADAS (R$)", "value": totals.get("entryValue")},
        {"label": "QTD. SAÍDAS", "value": totals.get("outputQuantity")},
        {"label": "VALOR SAÍDAS (R$)", "value": totals.get("outputValue")},
        {"label": "QTD. LÍQUIDA", "value": totals.get("netQuantity")},
        {"label": "VALOR LÍQUIDO (R$)", "value": totals.get("netValue")},
        {
            "label": "VALOR INICIAL (R$)",
            "value": totals.get("openingValue"),
        },
        {
            "label": "VALOR FINAL (R$)",
            "value": totals.get("closingValue"),
        },
    ]
    blocks = payload.get("blocks") or []
    sections = [
        ReportTableSection(
            title="Totais do período",
            columns=list(_PDF_TOTALS_COLUMNS),
            rows=totals_rows,
            align_right_keys=frozenset({"value"}),
            keep_together=True,
        ),
        ReportTableSection(
            title="Blocos por produto (página exportada)",
            columns=list(_PDF_BLOCK_COLUMNS),
            rows=[
                {key: block.get(key) for key, _ in _PDF_BLOCK_COLUMNS}
                for block in blocks
            ],
            align_right_keys=_PDF_BLOCK_NUMERIC,
            money_keys=_PDF_BLOCK_MONEY,
            quantity_keys=(
                _PDF_BLOCK_NUMERIC - _PDF_BLOCK_MONEY
            ),
        ),
        ReportTableSection(
            title="Movimentações",
            columns=list(_PDF_ITEM_COLUMNS),
            rows=[
                {key: item.get(key) for key, _ in _PDF_ITEM_COLUMNS}
                for item in payload.get("items") or []
            ],
            align_right_keys=_PDF_ITEM_NUMERIC,
            money_keys=_PDF_ITEM_MONEY,
            quantity_keys=(
                frozenset(
                    {
                        "entryQuantity",
                        "outputQuantity",
                        "runningQuantity",
                    }
                )
            ),
        ),
    ]
    return build_pdf(
        title=title,
        payload=payload,
        hashed_keys=_HASHED_KEYS,
        sections=sections,
        generated_by=generated_by,
        extra_metadata=(
            [("Armazém", payload.get("warehouse"))]
            if payload.get("warehouse")
            else None
        ),
    )
