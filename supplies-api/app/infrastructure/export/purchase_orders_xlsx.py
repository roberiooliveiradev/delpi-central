from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import Workbook

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EXPORT_FILENAME = "purchase-orders.xlsx"

_COLUMNS: tuple[tuple[str, str], ...] = (
    ("branch", "Filial"),
    ("order_number", "PC"),
    ("order_item", "Item"),
    ("product_code", "Produto"),
    ("product_description", "Descrição"),
    ("supplier_name", "Fornecedor"),
    ("open_quantity", "Saldo"),
    ("expected_delivery_date", "Prometida"),
    ("delivery_status", "Situação"),
    ("open_value", "Valor aberto"),
)


def build_purchase_orders_xlsx(items: list[dict[str, Any]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Pedidos"
    sheet.append([label for _key, label in _COLUMNS])
    for row in items:
        sheet.append([row.get(key) for key, _label in _COLUMNS])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
