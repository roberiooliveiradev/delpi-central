"""CSV/PDF export of the R08 work-in-process report (doc 119 §8.C policy).

Single engine: composes ``GetWorkInProcessUseCase`` unpaginated and
serializes the SAME payload the query returns — the shared MATR989
composition, never an export-only formula.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    EXPORT_FORMAT_CSV,
    EXPORT_PAGE_SIZE,
    EXPORTABLE_STATUSES,
    ReportExportTruncatedError,
    ReportNotExportableError,
    build_pdf,
    content_hash,
    csv_safe_text,
    scope_label,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .get_work_in_process_use_case import GetWorkInProcessUseCase

_HASHED_KEYS = (
    "physicalTotal",
    "allocatedTotal",
    "grandTotal",
    "items",
    "summariesByType",
)

_ITEM_COLUMNS = (
    ("branchCode", "Filial"),
    ("productCode", "Produto"),
    ("description", "Descrição"),
    ("productType", "Tipo"),
    ("productionOrder", "Ordem de Produção"),
    ("allocatedQuantity", "Qtd. Alocada"),
    ("allocatedValue", "Valor Alocado"),
)
_ITEM_NUMERIC_KEYS = frozenset({"allocatedQuantity", "allocatedValue"})

_TYPE_COLUMNS = (
    ("productType", "Tipo"),
    ("physicalValue", "Físico Proc."),
    ("allocatedValue", "Alocado OP"),
    ("totalValue", "Total"),
    ("openOrderCount", "OPs Abertas"),
)
_TYPE_NUMERIC_KEYS = frozenset(
    {"physicalValue", "allocatedValue", "totalValue", "openOrderCount"}
)


def export_filename(payload: dict[str, Any], export_format: str) -> str:
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    scope = payload.get("reportScope") or "all_products"
    return f"r08-work-in-process-{period}-{branch}-{scope}.{export_format}"


class ExportWorkInProcessUseCase:
    """Runs the shared MATR989 engine unpaginated and serializes it."""

    def __init__(self, get_use_case: GetWorkInProcessUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: StockInventoryQueryRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        unpaged = StockInventoryQueryRequest(
            period=request.period,
            branch=request.branch,
            report_scope=request.report_scope,
            warehouse=request.warehouse,
            page=1,
            page_size=EXPORT_PAGE_SIZE,
        )
        result = self._get_use_case.execute(
            unpaged, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise ReportNotExportableError(
                f"status={payload.get('status')}"
            )
        total_items = int(
            (payload.get("pagination") or {}).get("total_items") or 0
        )
        if len(payload.get("items") or []) < total_items:
            raise ReportExportTruncatedError(
                f"items={len(payload.get('items') or [])} "
                f"total_items={total_items}"
            )

        if export_format == EXPORT_FORMAT_CSV:
            stream = _build_csv(payload, generated_by=user_subject)
            content_type = "text/csv; charset=utf-8"
        else:
            stream = build_pdf(
                title="R08 — MATERIAL EM PROCESSO (MATR989)",
                payload=payload,
                hashed_keys=_HASHED_KEYS,
                sections=[
                    _type_section(payload),
                    _items_section(payload),
                ],
                generated_by=user_subject,
            )
            content_type = "application/pdf"

        return {
            "stream": stream,
            "content_type": content_type,
            "filename": export_filename(payload, export_format),
            "exported_count": len(payload.get("items") or []),
        }


def _type_section(payload: dict[str, Any]) -> ReportTableSection:
    rows = [
        {key: row.get(key) for key, _ in _TYPE_COLUMNS}
        for row in payload.get("summariesByType") or []
    ]
    return ReportTableSection(
        title="Material em processo por tipo de produto",
        columns=list(_TYPE_COLUMNS),
        rows=rows,
        totals_row={
            "productType": "TOTAL",
            "physicalValue": payload.get("physicalTotal"),
            "allocatedValue": payload.get("allocatedTotal"),
            "totalValue": payload.get("grandTotal"),
            "openOrderCount": sum(
                row.get("openOrderCount") or 0
                for row in payload.get("summariesByType") or []
            ),
        },
        align_right_keys=_TYPE_NUMERIC_KEYS,
        money_keys=frozenset(
            {"physicalValue", "allocatedValue", "totalValue"}
        ),
    )


def _items_section(payload: dict[str, Any]) -> ReportTableSection:
    rows = [
        {key: item.get(key) for key, _ in _ITEM_COLUMNS}
        for item in payload.get("items") or []
    ]
    return ReportTableSection(
        title="Saldo alocado por ordem de produção (bloco com-OP)",
        columns=list(_ITEM_COLUMNS),
        rows=rows,
        align_right_keys=_ITEM_NUMERIC_KEYS,
        money_keys=frozenset({"allocatedValue"}),
        quantity_keys=frozenset({"allocatedQuantity"}),
    )


def _build_csv(payload: dict[str, Any], *, generated_by: str | None) -> io.BytesIO:
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provenance = payload.get("provenance") or {}
    parity_status = payload.get("parityStatus") or "UNVERIFIED"
    official = bool(payload.get("officialMatr989"))
    branches_missing = payload.get("branchesMissing") or []

    buffer = io.StringIO()
    write = buffer.write

    write("# RELATORIO R08 — MATERIAL EM PROCESSO (MATR989)\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# escopo={payload.get('reportScope')}\n")
    write(f"# escopo_rotulo={scope_label(payload.get('reportScope'))}\n")
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
    write(f"# gerado_por={generated_by or 'desconhecido'}\n")
    write(f"# gerado_em={stamp}\n")
    write(f"# hash_conteudo_sha256={content_hash(payload, _HASHED_KEYS)}\n")
    if not official:
        write(
            "# AVISO: DOCUMENTO NAO OFICIAL — paridade pendente de "
            "homologacao contra nova emissao MATR989; nao substitui o "
            "relatorio oficial do Protheus.\n"
        )
    if branches_missing:
        write(
            "# AVISO: exportacao parcial — filiais sem snapshot "
            "declaradas acima; ausencia nao equivale a valor zero.\n"
        )
    write("\n")

    write("# RESUMO POR TIPO\n")
    fieldnames = [key for key, _ in _TYPE_COLUMNS]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in payload.get("summariesByType") or []:
        writer.writerow(
            {key: csv_safe_text(row.get(key)) for key in fieldnames}
        )
    write("\n")

    write("# TOTALIZADORES\n")
    write(f"# fisico_processo={payload.get('physicalTotal')}\n")
    write(f"# alocado_op={payload.get('allocatedTotal')}\n")
    write(f"# total_geral={payload.get('grandTotal')}\n")
    write("\n")

    write("# DETALHE POR ORDEM DE PRODUCAO\n")
    fieldnames = [key for key, _ in _ITEM_COLUMNS]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in payload.get("items") or []:
        writer.writerow(
            {key: csv_safe_text(item.get(key)) for key in fieldnames}
        )
    write("\n")

    output = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return output
