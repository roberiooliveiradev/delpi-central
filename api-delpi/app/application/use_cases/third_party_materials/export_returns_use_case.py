from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from openpyxl import Workbook

from app.application.dto.third_party_materials.constantes import (
    EXPORT_FORMAT_CSV,
    MAX_EXPORT_ROWS,
)
from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.domain.ports.third_party_materials.third_party_materials_query_repository_port import (
    ThirdPartyMaterialsQueryRepositoryPort,
)
from app.domain.services.third_party_materials.third_party_materials_shipment_mapper import (
    flatten_export_rows,
    group_shipment_rows,
)

EXPORT_COLUMNS = (
    "shipment_recno",
    "shipment_id",
    "branch",
    "product_code",
    "customer_reference",
    "product_description",
    "partner_code",
    "partner_store",
    "partner_name",
    "receipt_number",
    "receipt_series",
    "receipt_issued_on",
    "received_quantity",
    "returned_quantity",
    "pending_balance",
    "status",
    "control_difference",
    "return_recno",
    "return_number",
    "return_series",
    "return_issued_on",
    "return_tes",
    "return_quantity",
    "return_partner_type",
)

BALANCE_REPEAT_NOTICE = (
    "Saldo e quantidades da remessa se repetem em cada linha de retorno. "
    "Não some pending_balance / received_quantity nas linhas detalhadas."
)


class ExportThirdPartyMaterialsReturnsUseCase:
    def __init__(self, repository: ThirdPartyMaterialsQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: ThirdPartyMaterialsQueryRequest) -> dict:
        rows = self._repository.list_export_rows(request, limit=MAX_EXPORT_ROWS)
        shipments = group_shipment_rows(rows)
        export_rows = flatten_export_rows(shipments)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        if request.export_format == EXPORT_FORMAT_CSV:
            stream = _build_csv(export_rows)
            return {
                "stream": stream,
                "content_type": "text/csv; charset=utf-8",
                "filename": f"materiais-terceiros-retornos-{stamp}.csv",
                "exported_count": len(export_rows),
            }
        stream = _build_xlsx(export_rows)
        return {
            "stream": stream,
            "content_type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "filename": f"materiais-terceiros-retornos-{stamp}.xlsx",
            "exported_count": len(export_rows),
        }


def _build_csv(rows: list[dict]) -> io.BytesIO:
    buffer = io.StringIO()
    buffer.write(f"# {BALANCE_REPEAT_NOTICE}\n")
    writer = csv.DictWriter(buffer, fieldnames=list(EXPORT_COLUMNS), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    payload = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    payload.seek(0)
    return payload


def _build_xlsx(rows: list[dict]) -> io.BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "retornos"
    sheet["A1"] = BALANCE_REPEAT_NOTICE
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(EXPORT_COLUMNS))
    sheet.append(list(EXPORT_COLUMNS))
    for row in rows:
        sheet.append([row.get(column) for column in EXPORT_COLUMNS])
    payload = io.BytesIO()
    workbook.save(payload)
    payload.seek(0)
    return payload
