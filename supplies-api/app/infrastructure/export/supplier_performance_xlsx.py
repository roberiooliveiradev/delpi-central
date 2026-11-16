"""Formatted evidence workbook for supplier IDF. No formula interpretation of ERP text."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EXPORT_FILENAME = "idf-fornecedores.xlsx"
NAVY = "023667"
CYAN = "00A6DE"
LIGHT = "EEF8FC"
ALTERNATE = "F7FAFD"
BORDER = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)
SUMMARY_COLUMNS = (
    ("supplier_code", "Cód. fornecedor", "id"),
    ("supplier_store", "Loja", "id"),
    ("supplier_name", "Fornecedor", "text"),
    ("branches", "Filiais", "list"),
    ("quality.assessed_count", "Inspeções concluídas", "int"),
    ("quality.positive_count", "Inspeções aprovadas", "int"),
    ("quality.negative_count", "Inspeções rejeitadas", "int"),
    ("quality.conditional_count", "Laudos condicionais", "int"),
    ("quality.urgent_count", "Liberações urgentes", "int"),
    ("quality.unknown_count", "Inspeções a revisar", "int"),
    ("quality.index", "Qualidade (%)", "percent"),
    ("quality_contribution", "Peso Qualidade (pontos)", "points"),
    ("delivery.assessed_count", "Linhas recebidas", "int"),
    ("delivery.positive_count", "Linhas no prazo", "int"),
    ("delivery.negative_count", "Linhas fora do prazo", "int"),
    ("delivery.unknown_count", "Recebimentos sem data", "int"),
    ("delivery.index", "Entrega (%)", "percent"),
    ("delivery_contribution", "Peso Entrega (pontos)", "points"),
    ("idf", "IDF (0–100)", "points"),
    ("status", "Disponibilidade", "coverage"),
)
DELIVERY_COLUMNS = (
    ("branch", "Filial", "id"),
    ("supplier_code", "Cód. fornecedor", "id"),
    ("supplier_store", "Loja", "id"),
    ("supplier_name", "Fornecedor", "text"),
    ("document", "Documento de entrada (OTD)", "id"),
    ("order_number", "Pedido de compra", "id"),
    ("order_item", "Item PC", "id"),
    ("product_code", "Cód. produto", "id"),
    ("product_description", "Descrição do produto", "text"),
    ("product_type", "Tipo de produto", "text"),
    ("quantity", "Quantidade", "qty"),
    ("order_issue_date", "Emissão do pedido", "date"),
    ("expected_delivery_date", "Entrega prevista", "date"),
    ("receipt_entry_date", "Digitação do recebimento", "date"),
    ("invoice_issue_date", "Emissão da NF", "date"),
    ("days_diff", "Dias de diferença (OTD)", "days"),
    ("evidence_state", "Situação da entrega", "text"),
)
INSPECTION_COLUMNS = (
    ("branch", "Filial", "id"),
    ("supplier_code", "Cód. fornecedor", "id"),
    ("supplier_store", "Loja", "id"),
    ("supplier_name", "Fornecedor", "text"),
    ("inspection_id", "Identificador da inspeção", "id"),
    ("invoice_number", "Nota fiscal", "id"),
    ("invoice_series", "Série NF", "id"),
    ("invoice_item", "Item NF", "id"),
    ("product_code", "Cód. produto", "id"),
    ("lot", "Lote", "id"),
    ("supplier_lot", "Lote fornecedor", "id"),
    ("quantity", "Quantidade", "qty"),
    ("unit", "Unidade", "text"),
    ("receipt_date", "Recebimento", "date"),
    ("report_date", "Data do laudo", "date"),
    ("report_time", "Hora do laudo", "text"),
    ("evidence_state", "Resultado no IDF", "text"),
    ("situation_code", "Cód. situação", "id"),
    ("inspection_status", "Situação da inspeção", "text"),
    ("result_summary", "Resultado resumo", "text"),
    ("report_code", "Código do laudo", "id"),
    ("inspector", "Ensaiador", "text"),
    ("test_count", "Qtde. ensaios", "int"),
    ("rejected_test_count", "Ensaios reprovados", "int"),
    ("conditional", "Laudo condicional", "yesno"),
    ("urgent", "Liberação urgente", "yesno"),
    ("report_justification", "Justificativa", "text"),
)
COVERAGE = {
    "complete": "IDF calculado",
    "missing_quality": "Sem inspeções concluídas",
    "missing_delivery": "Sem recebimentos",
    "inconsistent": "Dados a revisar",
}


def _deep(row: dict, path: str) -> Any:
    value: Any = row
    for token in path.split("."):
        value = value.get(token) if isinstance(value, dict) else None
    return value


def _cell_value(value: Any, kind: str):
    if value is None or value == "":
        return None
    if kind == "coverage":
        return COVERAGE.get(str(value), str(value))
    if kind == "list":
        return ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    if kind == "yesno":
        return "Sim" if value in (1, True, "1") else "Não"
    if kind == "date":
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return str(value)[:80]
    if kind in {"percent", "points", "qty", "days", "int"}:
        try:
            return int(value) if kind == "int" else float(value)
        except (TypeError, ValueError):
            return None
    # Identifiers must remain text to preserve leading zeros; guard formula injection.
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        text = "'" + text
    return text[:32000]


def _width(label: str, kind: str) -> float:
    if kind == "date":
        return 17
    if kind in ("qty", "percent", "points", "days", "int"):
        return min(25, max(14, len(label) + 2))
    return min(38, max(15, len(label) + 3))


def _sheet(workbook: Workbook, title: str, columns, rows, scope: str, period: str, calculated_at: str):
    ws = workbook.create_sheet(title)
    ws.sheet_view.showGridLines = False
    n = len(columns)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
    heading = ws.cell(1, 1, f"DELPI  |  {title.upper()}")
    heading.font = Font(name="Aptos Display", size=17, bold=True, color="FFFFFF")
    heading.fill = PatternFill("solid", fgColor=NAVY)
    heading.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 35
    # Fill merged cells as well, so the entire title ribbon renders in Excel.
    for col in range(2, n + 1):
        ws.cell(1, col).fill = PatternFill("solid", fgColor=NAVY)
    for row_number, label in (
        (2, f"Período: {period}    |    Filiais: {scope}"),
        (3, f"Gerado em: {calculated_at}    |    Fonte: IDF / Portal de Suprimentos"),
    ):
        ws.merge_cells(start_row=row_number, start_column=1, end_row=row_number, end_column=n)
        c = ws.cell(row_number, 1, label)
        c.font = Font(name="Aptos", size=10, bold=(row_number == 2), color=NAVY)
        c.alignment = Alignment(indent=1, vertical="center")
        ws.row_dimensions[row_number].height = 23
    ws.row_dimensions[4].height = 10
    for col, (_, label, kind) in enumerate(columns, start=1):
        c = ws.cell(5, col, label)
        c.fill = PatternFill("solid", fgColor=CYAN)
        c.font = Font(name="Aptos", bold=True, color="FFFFFF", size=10)
        c.border = BORDER
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = _width(label, kind)
    ws.row_dimensions[5].height = 35
    for index, item in enumerate(rows, start=6):
        alternate = index % 2 == 1
        for col, (key, _, kind) in enumerate(columns, start=1):
            c = ws.cell(index, col, _cell_value(_deep(item, key), kind))
            c.font = Font(name="Aptos", size=10, color="184C45" if kind != "id" else NAVY)
            c.fill = PatternFill("solid", fgColor=ALTERNATE if alternate else "FFFFFF")
            c.border = BORDER
            c.alignment = Alignment(vertical="center", wrap_text=kind == "text")
            if kind == "date" and isinstance(c.value, date):
                c.number_format = "DD/MM/YYYY"
            elif kind in ("percent", "points"):
                c.number_format = '0.00"%"' if kind == "percent" else "0.00"
            elif kind == "qty":
                c.number_format = "#,##0.00"
            elif kind == "days":
                c.number_format = '+0.##;-0.##;0'
            elif kind == "int":
                c.number_format = "#,##0"
            elif kind == "id":
                c.number_format = "@"
        ws.row_dimensions[index].height = 23
    ws.freeze_panes = "E6" if n > 4 else "A6"
    ws.auto_filter.ref = f"A5:{get_column_letter(n)}{max(5, ws.max_row)}"
    ws.print_title_rows = "1:5"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    return ws


def _criteria_sheet(wb: Workbook, data: dict, selected: str):
    rows = [
        ("Fórmula", "IDF = Qualidade × 70% + Entrega × 30%; escala 0–100"),
        ("Fornecedor", selected),
        ("Qualidade", "Inspeções aprovadas / concluídas, por data do laudo"),
        ("Situações aceitas", "Aprovação normal, laudo condicional e liberação urgente"),
        ("Inspeção", "Uma linha por filial + ID da inspeção + fornecedor + loja"),
        ("Entrega", "Linhas no prazo ou antecipadas / linhas recebidas, por data de digitação"),
        ("Documento", "Documento da view de pontualidade; não presumir equivalência com NF ou laudo"),
        ("Pedido de compra", "Número e item do PC disponíveis somente na evidência de recebimento"),
        ("Datas", "Entrega prevista, digitação, emissão de PC/NF, laudo e recebimento"),
        ("Vínculo", "Abas independentes: não há associação artificial entre um laudo e um pedido"),
        ("Faltas", "Sem uma das bases ou com registros inconsistentes, IDF permanece em branco"),
        ("Limite", "Exportação limitada a 12.000 inspeções e 12.000 recebimentos por recorte"),
        ("Escopo", "As linhas seguem estritamente a consulta IDF vigente em produção"),
        ("Atenção", "O filtro de produto documentado no OTD geral diverge da consulta de Entrega atual do IDF; revisar em alteração separada"),
        ("Média", "Média simples dos fornecedores/lojas com IDF completo"),
    ]
    ws = wb.create_sheet("Critérios")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:B1")
    ws["A1"] = "DELPI  |  METODOLOGIA DO IDF"
    ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
    ws["A1"].font = Font(name="Aptos Display", size=16, bold=True, color="FFFFFF")
    ws["A1"].alignment = Alignment(indent=1, vertical="center")
    ws["B1"].fill = PatternFill("solid", fgColor=NAVY)
    ws.row_dimensions[1].height = 36
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 110
    for index, (key, value) in enumerate(rows, start=3):
        for col, text in enumerate((key, value), 1):
            cell = ws.cell(index, col, text)
            cell.border = BORDER
            cell.fill = PatternFill("solid", fgColor=LIGHT if col == 1 else ("FFFFFF" if index % 2 == 0 else ALTERNATE))
            cell.font = Font(name="Aptos", size=10, bold=col == 1, color=NAVY)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[index].height = 31 if len(value) > 95 else 25
    ws.freeze_panes = "B3"
    return ws


def build_supplier_performance_xlsx(data: dict) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "IDF de fornecedores | DELPI"
    wb.properties.subject = "Índice de Desempenho do Fornecedor com evidências"
    scope = ", ".join(data.get("branches") or [])
    period_data = data.get("period") or {}
    period = f"{period_data.get('from', '')} a {period_data.get('to', '')}"
    calculated_at = str(data.get("calculated_at") or "")[:19].replace("T", " ")
    selected_obj = data.get("supplier_selected")
    selected = (
        f"{selected_obj.get('code')} / loja {selected_obj.get('store')}"
        if isinstance(selected_obj, dict) else "Todos os fornecedores"
    )
    scope = f"{scope}    |    Fornecedor: {selected}"
    _sheet(wb, "Resumo IDF", SUMMARY_COLUMNS, data.get("items") or [], scope, period, calculated_at)
    _sheet(wb, "Entregas", DELIVERY_COLUMNS, data.get("deliveries") or [], scope, period, calculated_at)
    _sheet(wb, "Inspeções", INSPECTION_COLUMNS, data.get("inspections") or [], scope, period, calculated_at)
    _criteria_sheet(wb, data, selected)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
