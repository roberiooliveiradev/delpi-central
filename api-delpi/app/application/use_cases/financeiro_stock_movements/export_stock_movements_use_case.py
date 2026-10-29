"""CSV/PDF export of the R05 stock-movements report (doc 119 §8.C policy).

Single engine: this use case composes ``GetStockMovementsUseCase`` and
serializes the SAME payload the query returns — no second calculation,
no export-only formula. Metadata identity, SHA-256 content hash and
the parity watermark are stamped by the shared export machinery.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from app.application.dto.financeiro_stock_movements.stock_movements_request import (
    StockMovementsQueryRequest,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    EXPORT_FORMAT_CSV,
    EXPORTABLE_STATUSES,
    ReportNotExportableError,
    build_pdf,
    content_hash,
    csv_safe_text,
    scope_label,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ReportTableSection,
)

from .get_stock_movements_use_case import GetStockMovementsUseCase

_HASHED_KEYS = ("rows", "totals")

_ROW_COLUMNS = (
    ("productType", "Tipo"),
    ("openingBalance", "Saldo Inicial"),
    ("purchases", "Compras"),
    ("internalMovements", "Mov. Internas"),
    ("productionRequisitions", "Requisições"),
    ("transfers", "Transferências"),
    ("production", "Produção"),
    ("sales", "Vendas"),
    ("processTransfersMemo", "Transf. Processo (memo)"),
    ("salesReturns", "Dev. Vendas"),
    ("purchaseReturns", "Dev. Compras"),
    ("thirdPartyIn", "Ent. Poder 3º"),
    ("thirdPartyOut", "Saída Poder 3º"),
    ("closingBalance", "Saldo Atual"),
    ("netMovement", "Mov. Líquida"),
)
_NUMERIC_KEYS = frozenset(
    key for key, _ in _ROW_COLUMNS if key != "productType"
)


def export_filename(payload: dict[str, Any], export_format: str) -> str:
    period = payload.get("period") or "unknown"
    branch = payload.get("branchCode") or "all"
    scope = payload.get("reportScope") or "all_products"
    return f"r05-stock-movements-{period}-{branch}-{scope}.{export_format}"


class ExportStockMovementsUseCase:
    """Runs the shared R05 engine and serializes its payload."""

    def __init__(self, get_use_case: GetStockMovementsUseCase) -> None:
        self._get_use_case = get_use_case

    def execute(
        self,
        request: StockMovementsQueryRequest,
        *,
        export_format: str = EXPORT_FORMAT_CSV,
        user_subject: str | None,
    ) -> dict:
        result = self._get_use_case.execute(
            request, user_subject=user_subject
        )
        payload = result.to_dict()

        if payload.get("status") not in EXPORTABLE_STATUSES:
            raise ReportNotExportableError(
                f"status={payload.get('status')}"
            )

        if export_format == EXPORT_FORMAT_CSV:
            stream = _build_csv(payload, generated_by=user_subject)
            content_type = "text/csv; charset=utf-8"
        else:
            stream = build_pdf(
                title="R05 — ENTRADAS E SAÍDAS (MOVIMENTAÇÃO DE ESTOQUE)",
                payload=payload,
                hashed_keys=_HASHED_KEYS,
                sections=[_rows_section(payload)],
                generated_by=user_subject,
            )
            content_type = "application/pdf"

        return {
            "stream": stream,
            "content_type": content_type,
            "filename": export_filename(payload, export_format),
            "exported_count": len(payload.get("rows") or []),
        }


def _rows_section(payload: dict[str, Any]) -> ReportTableSection:
    rows = [
        {key: row.get(key) for key, _ in _ROW_COLUMNS}
        for row in payload.get("rows") or []
    ]
    totals = payload.get("totals") or {}
    totals_row = {"productType": "TOTAL"}
    for key, _label in _ROW_COLUMNS[1:]:
        totals_row[key] = totals.get(key)
    return ReportTableSection(
        title="Movimentação por tipo de produto",
        columns=list(_ROW_COLUMNS),
        rows=rows,
        totals_row=totals_row,
        align_right_keys=_NUMERIC_KEYS,
        money_keys=_NUMERIC_KEYS,
    )


def _build_csv(payload: dict[str, Any], *, generated_by: str | None) -> io.BytesIO:
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provenance = payload.get("provenance") or {}
    parity_status = payload.get("parityStatus") or "UNVERIFIED"
    official = bool(payload.get("officialMatr320"))
    branches_missing = payload.get("branchesMissing") or []

    buffer = io.StringIO()
    write = buffer.write

    write("# RELATORIO R05 — ENTRADAS E SAIDAS (MOVIMENTACAO DE ESTOQUE)\n")
    write(f"# competencia={payload.get('period')}\n")
    write(f"# filial={payload.get('branchCode')}\n")
    write(f"# escopo={payload.get('reportScope')}\n")
    write(f"# escopo_rotulo={scope_label(payload.get('reportScope'))}\n")
    write(f"# data_fechamento={payload.get('dataAsOf')}\n")
    write(f"# produtor_oficial={provenance.get('officialProducer')}\n")
    write(f"# procedimento_oficial={provenance.get('officialProcedure')}\n")
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
            "homologacao contra nova emissao MATR320; nao substitui o "
            "relatorio oficial do Protheus.\n"
        )
    if branches_missing:
        write(
            "# AVISO: exportacao parcial — filiais sem snapshot "
            "declaradas acima; ausencia nao equivale a valor zero.\n"
        )
    write("\n")

    fieldnames = [key for key, _ in _ROW_COLUMNS]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in payload.get("rows") or []:
        writer.writerow(
            {
                key: csv_safe_text(row.get(key))
                for key in fieldnames
            }
        )
    write("\n")

    write("# TOTALIZADORES\n")
    totals = payload.get("totals") or {}
    for key, _label in _ROW_COLUMNS[1:]:
        write(f"# {key}={totals.get(key)}\n")

    output = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return output
