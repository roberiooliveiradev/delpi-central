"""Consolidated outstanding third-party materials by supplier and product."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.application.dto.third_party_materials.constantes import (
    EXPORT_FORMAT_CSV,
    MAX_EXPORT_ROWS,
)
from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    build_pagination,
)
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    as_quantity,
)

EXPORT_COLUMNS = (
    ("branch", "Filial"),
    ("supplier_code", "Fornecedor"),
    ("supplier_store", "Loja"),
    ("supplier_name", "Razão social"),
    ("product_code", "Produto"),
    ("product_description", "Descrição"),
    ("unit", "UM"),
    ("shipment_count", "Remessas pendentes"),
    ("received_quantity", "Quantidade recebida"),
    ("returned_quantity", "Quantidade devolvida"),
    ("pending_quantity", "Saldo pendente"),
)


def _map_item(row: dict, branch: str) -> dict:
    return {
        "branch": branch,
        "supplier_code": str(row.get("supplier_code") or "").strip(),
        "supplier_store": str(row.get("supplier_store") or "").strip(),
        "supplier_name": str(row.get("supplier_name") or "").strip(),
        "product_code": str(row.get("product_code") or "").strip(),
        "product_description": str(row.get("product_description") or "").strip(),
        "unit": str(row.get("unit") or "").strip(),
        "shipment_count": int(row.get("shipment_count") or 0),
        "received_quantity": as_quantity(row.get("received_quantity")),
        "returned_quantity": as_quantity(row.get("returned_quantity")),
        "pending_quantity": as_quantity(row.get("pending_quantity")),
    }


class PendingSupplierReportUseCase:
    def __init__(self, repository: ThirdPartyMaterialsQueryRepositoryPort) -> None:
        self._repository = repository

    def _summary(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        row = self._repository.get_pending_report_summary(request)
        unit_count = int(row.get("unit_count") or 0)
        # Never totalize kilograms, meters and pieces into a single quantity.
        return {
            "supplier_count": int(row.get("supplier_count") or 0),
            "product_count": int(row.get("product_count") or 0),
            "shipment_count": int(row.get("shipment_count") or 0),
            "pending_quantity": (
                as_quantity(row.get("pending_quantity")) if unit_count == 1 else None
            ),
            "unit": str(row.get("unit") or "").strip() if unit_count == 1 else None,
            "mixed_units": unit_count > 1,
        }

    def execute(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        summary = self._summary(request)
        rows = self._repository.list_pending_report_rows(request)
        return {
            "items": [_map_item(row, request.branch) for row in rows],
            "summary": summary,
            **build_pagination(
                page=request.page,
                page_size=request.page_size,
                total_items=summary["product_count"],
            ),
        }

    def export(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        summary = self._summary(request)
        if summary["product_count"] > MAX_EXPORT_ROWS:
            raise ValueError(
                "Relatório excede o limite seguro de exportação. "
                "Restrinja por fornecedor ou produto; nenhum registro foi omitido."
            )
        rows = self._repository.list_pending_export_rows(request, limit=MAX_EXPORT_ROWS)
        items = [_map_item(row, request.branch) for row in rows]
        if len(items) != summary["product_count"]:
            raise ValueError(
                "A quantidade de registros mudou durante a consulta. "
                "Atualize o relatório e tente exportar novamente."
            )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        if request.export_format == EXPORT_FORMAT_CSV:
            stream = _csv(items)
            media_type = "text/csv; charset=utf-8"
            extension = "csv"
        else:
            stream = _excel(items)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        return {
            "stream": stream,
            "content_type": media_type,
            "filename": f"materiais-terceiros-pendencias-fornecedor-{stamp}.{extension}",
            "exported_count": len(items),
        }


def _csv(items: list[dict]) -> io.BytesIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([label for _, label in EXPORT_COLUMNS])
    for item in items:
        writer.writerow([item.get(key) for key, _ in EXPORT_COLUMNS])
    stream = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    stream.seek(0)
    return stream


def _excel(items: list[dict]) -> io.BytesIO:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Pendências por fornecedor"
    worksheet.append([label for _, label in EXPORT_COLUMNS])
    for item in items:
        worksheet.append([item.get(key) for key, _ in EXPORT_COLUMNS])

    for cell in worksheet[1]:
        cell.fill = PatternFill("solid", fgColor="023667")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(vertical="center")
    worksheet.row_dimensions[1].height = 29
    widths = (12, 17, 10, 44, 18, 53, 10, 22, 24, 24, 24)
    for col, width in enumerate(widths, start=1):
        worksheet.column_dimensions[worksheet.cell(1, col).column_letter].width = width
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream
