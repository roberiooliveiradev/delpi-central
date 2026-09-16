from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import Workbook

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EXPORT_FILENAME = "purchase-requests.xlsx"

_COLUMNS: tuple[tuple[str, str], ...] = (
    ("branch", "Filial"),
    ("request_number", "SC"),
    ("request_item", "Item"),
    ("product_code", "Produto"),
    ("product_description", "Descrição"),
    ("requester", "Solicitante"),
    ("cost_center", "Centro de custo"),
    ("issue_date", "Abertura"),
    ("overall_stage", "Situação"),
    ("approval_status", "Aprovação"),
)


def _cell(item: dict[str, Any], key: str) -> Any:
    if key == "requester":
        requester = item.get("requester") if isinstance(item.get("requester"), dict) else {}
        return (requester or {}).get("name") or ""
    if key == "cost_center":
        cost_center = item.get("cost_center") if isinstance(item.get("cost_center"), dict) else {}
        return (cost_center or {}).get("code") or item.get("cost_center_code") or ""
    if key == "issue_date":
        return item.get("request_issue_date") or item.get("issue_date") or ""
    if key == "overall_stage":
        derived = item.get("derived") if isinstance(item.get("derived"), dict) else {}
        return (derived or {}).get("overall_stage") or item.get("overall_stage") or ""
    if key == "approval_status":
        approval = item.get("approval") if isinstance(item.get("approval"), dict) else {}
        return (approval or {}).get("status") or ""
    return item.get(key) or ""


def build_purchase_requests_xlsx(items: list[dict[str, Any]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Solicitacoes"
    sheet.append([label for _key, label in _COLUMNS])
    for row in items:
        sheet.append([_cell(row, key) for key, _label in _COLUMNS])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
