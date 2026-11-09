"""Excel institucional para análise de NCs por operador (GLPI #1538).

Dados provenientes da mesma agregação SQL que alimenta o ranking, sem
paginação. A coluna de quantidade é QI2_QTDDEV (devolvida/rejeitada).
"""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

NAVY = "023667"
WHITE = "FFFFFF"
INK = "1F2937"
LIGHT = "EAF4FA"
PALE = "F6FAFD"
EDGE = "C8D9E8"
THIN = Side(style="thin", color=EDGE)
GRID = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _safe_text(value: object) -> str:
    """Nunca executar textos livres (descrições/nomes) como fórmulas do Excel."""
    text = ILLEGAL_CHARACTERS_RE.sub("", str(value or ""))[:32760]
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def _filter_description(filters: dict) -> str:
    keys = [
        ("Filial", "branch"),
        ("Tipo", "type"),
        ("De", "date_start"),
        ("Até", "date_end"),
        ("Status", "status"),
        ("Item", "item_code"),
        ("Descrição", "description"),
    ]
    return " | ".join(
        f"{name}: {_safe_text(filters.get(key) or ('Todas' if key in ('branch', 'type') else '-'))}"
        for name, key in keys
    )


def _prepare_sheet(
    sheet,
    *,
    title: str,
    headers: list[str],
    rows: list[list],
    filters: dict,
    numeric_columns: set[int],
    quantity_columns: set[int],
) -> None:
    sheet.sheet_view.showGridLines = False
    last_col = len(headers)
    col = get_column_letter(last_col)
    sheet.merge_cells(f"A1:{col}1")
    sheet.merge_cells(f"A2:{col}2")
    sheet.merge_cells(f"A3:{col}3")
    sheet["A1"] = title
    sheet["A2"] = "Critério: mais NCs (reincidência) → maior quantidade rejeitada/devolvida → descrição"
    sheet["A3"] = _filter_description(filters)
    for row_index in (1, 2, 3):
        for cells in sheet.iter_rows(min_row=row_index, max_row=row_index, min_col=1, max_col=last_col):
            for cell in cells:
                cell.border = GRID
                cell.fill = PatternFill(
                    "solid", fgColor=NAVY if row_index == 1 else LIGHT
                )
        anchor = sheet.cell(row=row_index, column=1)
        anchor.alignment = Alignment(vertical="center", horizontal="left", indent=1)
        anchor.font = Font(
            name="Aptos",
            size=15 if row_index == 1 else 10,
            color=WHITE if row_index == 1 else INK,
            bold=row_index == 1,
        )
    sheet.row_dimensions[1].height = 34
    sheet.row_dimensions[2].height = 26
    sheet.row_dimensions[3].height = 24
    sheet.row_dimensions[4].height = 10

    header_row = 5
    for index, header in enumerate(headers, 1):
        cell = sheet.cell(row=header_row, column=index, value=header)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Aptos", color=WHITE, bold=True, size=10)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = GRID
    sheet.row_dimensions[header_row].height = 32

    effective_rows = rows or [["Sem registros para os filtros atuais"] + [""] * (last_col - 1)]
    widths = [max(13, len(label) + 3) for label in headers]
    for idx, values in enumerate(effective_rows, start=6):
        for col_index, raw in enumerate(values, 1):
            value = _safe_text(raw) if isinstance(raw, str) else raw
            cell = sheet.cell(row=idx, column=col_index, value=value)
            cell.border = GRID
            cell.fill = PatternFill("solid", fgColor=WHITE if idx % 2 == 0 else PALE)
            cell.font = Font(name="Aptos", color=INK, size=10)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if col_index in numeric_columns and isinstance(value, (int, float)):
                cell.number_format = "#,##0"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if col_index in quantity_columns and isinstance(value, (int, float)):
                cell.number_format = "#,##0.###"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            # Matrículas devem manter zeros à esquerda e não sofrer conversão.
            if col_index == 1:
                cell.number_format = "@"
            widths[col_index - 1] = max(
                widths[col_index - 1], min(len(str(value)) + 2, 58)
            )

    for idx, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(idx)].width = min(width, 58)
    sheet.freeze_panes = "A6"
    sheet.auto_filter.ref = f"A5:{col}{5 + len(effective_rows)}"
    sheet.print_options.horizontalCentered = True
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.sheet_properties.outlinePr.summaryBelow = True


def build_nonconformity_operator_excel(data: dict, *, filters: dict) -> bytes:
    """Gera duas abas completas: resumo por matrícula e detalhe por defeito."""
    wb = Workbook()
    overview = wb.active
    overview.title = "Resumo Operadores"
    details = wb.create_sheet("Defeitos por Operador")

    summary_headers = [
        "Matrícula",
        "Operador",
        "Total de NCs",
        "Tipos de defeito",
        "Principal defeito",
        "Reincidência do principal defeito",
        "Qtd. rejeitada/devolvida do principal",
        "Qtd. rejeitada/devolvida total",
    ]
    summary = [
        [
            r["operator_code"],
            r["operator_name"],
            r["total_ncs"],
            r["defect_types_count"],
            r["main_defect"],
            r["main_defect_count"],
            r["main_defect_rejected_quantity"],
            r["total_rejected_quantity"],
        ]
        for r in data.get("all_rows", [])
    ]
    _prepare_sheet(
        overview,
        title="Dashboard da Qualidade | NCs por operador",
        headers=summary_headers,
        rows=summary,
        filters=filters,
        numeric_columns={3, 4, 6},
        quantity_columns={7, 8},
    )

    detail_headers = [
        "Matrícula",
        "Operador",
        "Descrição do defeito",
        "Reincidência (NCs)",
        "Qtd. rejeitada/devolvida (QI2_QTDDEV)",
        "Principal defeito",
    ]
    detail_rows = [
        [
            r["operator_code"],
            r["operator_name"],
            r["defect"],
            r["nc_count"],
            r["rejected_quantity"],
            "Sim" if r["is_main_defect"] else "Não",
        ]
        for r in data.get("defect_rows", [])
    ]
    _prepare_sheet(
        details,
        title="Dashboard da Qualidade | Detalhamento dos defeitos",
        headers=detail_headers,
        rows=detail_rows,
        filters=filters,
        numeric_columns={4},
        quantity_columns={5},
    )
    wb.properties.title = "Não conformidades por operador - Delpi"
    wb.properties.subject = "Ranking completo e detalhamento de NC por operador"
    wb.properties.creator = "Dashboard da Qualidade - Minha Delpi"
    wb.properties.description = (
        "Dados filtrados da QI2010. Quantidade rejeitada/devolvida = QI2_QTDDEV."
    )
    output = BytesIO()
    wb.save(output)
    return output.getvalue()
