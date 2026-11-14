"""Planilha no layout da skill: mesmas abas e os mesmos cabeçalhos."""

from __future__ import annotations

import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

SHEETS = [
    ("Resumo", ["Indicador", "Quantidade", "Leitura"]),
    ("TES usadas", ["TES", "Descrição (SF4)", "Tipo do TES", "Cod. Fiscal", "CFOPs de entrada", "Itens DANFE", "Calcula ICMS", "Credita ICMS", "Livro ICMS", "Material de consumo", "Calcula IPI", "Credita IPI", "Livro IPI"]),
    ("Divergências", ["Severidade", "Ocorrência", "NF", "Série", "Fornecedor (XML)", "Campo", "Valor Protheus", "Valor XML", "Diferença (Protheus − XML)", "TES (SD1)", "O que fazer", "Chave de Acesso"]),
    ("Comparativo", ["Situação", "NF", "Série", "Fornecedor (XML)", "ICMS Protheus", "IPI Protheus", "Total Protheus", "Ocorrências", "Chave de Acesso"]),
    ("Só no XML", ["Situação", "NF", "Série", "Emitente", "Motivo / leitura", "Chave de Acesso"]),
    ("Só no SF1", ["Situação", "NF", "Série", "Fornecedor", "Motivo / leitura", "Chave NF-e"]),
    ("CT-e Comparativo", ["Situação", "CT-e", "Chave de Acesso", "Valor Protheus", "ICMS Protheus"]),
    ("Itens Divergências", ["Severidade", "Ocorrência", "NF", "Item SD1", "Campo", "Valor Protheus", "Valor XML", "TES", "Chave de Acesso"]),
    ("Itens Excluídos", ["Tipo de documento", "Documento", "Série", "Fornecedor", "Loja", "Itens", "Valor"]),
]


def build_workbook(payload: dict) -> bytes:
    rows = {name: [header] for name, header in SHEETS}
    summary = payload["analysis"]
    counts = {}
    for run in payload.get("runs") or []:
        pass
    occurrences = payload["occurrences"]
    rows["Resumo"].append(["Ocorrências", str(len(occurrences)), "Motor da auditoria de entradas"])
    rows["Resumo"].append(["Notas", str(len(payload["documents"])), f"{summary['date_from']} a {summary['date_to']}"])
    rows["Resumo"].append(["Sem par", str(len(payload["unmatched"])), "XML sem lançamento ou lançamento sem XML"])
    unavailable = sum(1 for row in payload["documents"] if row.get("situation") == "xml_unavailable")
    rows["Resumo"].append(["XML indisponível", str(unavailable), "A fonte não respondeu; não é nota sem par"])
    for row in payload["tes"]:
        sf4 = row.get("sf4") or {}
        rows["TES usadas"].append([
            row.get("tes_code"), sf4.get("description"), sf4.get("tes_type"), sf4.get("fiscal_code"),
            sf4.get("fiscal_code"), sf4.get("items"), sf4.get("calculates_icms"), sf4.get("credits_icms"),
            sf4.get("icms_book"), sf4.get("consumption_material"), sf4.get("calculates_ipi"),
            sf4.get("credits_ipi"), sf4.get("ipi_book"),
        ])
    for row in occurrences:
        target = "Itens Divergências" if row.get("item") else "Divergências"
        if row.get("item"):
            rows[target].append([row.get("severity"), row.get("title"), row.get("document_number"), row.get("item"), row.get("field_label"), row.get("protheus_value"), row.get("xml_value"), row.get("tes"), row.get("access_key")])
        else:
            rows[target].append([row.get("severity"), row.get("title"), row.get("document_number"), row.get("series"), row.get("supplier_name"), row.get("field_label"), row.get("protheus_value"), row.get("xml_value"), row.get("difference"), row.get("tes"), row.get("action"), row.get("access_key")])
    for row in payload["documents"]:
        comparison = row.get("comparison") or {}
        situation = "XML indisponível" if row.get("situation") == "xml_unavailable" else row.get("situation")
        rows["Comparativo"].append([situation, row.get("document_number"), row.get("series"), row.get("supplier_name"), comparison.get("icms"), comparison.get("ipi"), comparison.get("gross"), row.get("divergence_count"), row.get("access_key")])
    for row in payload["unmatched"]:
        sheet = "Só no XML" if row.get("side") == "xml" else "Só no SF1"
        if row.get("side") == "xml":
            rows[sheet].append([row.get("severity"), row.get("document_number"), row.get("series"), row.get("party_name"), row.get("reason"), row.get("access_key")])
        else:
            rows[sheet].append([row.get("severity"), row.get("document_number"), row.get("series"), row.get("party_name"), row.get("reason"), row.get("access_key")])
    for row in payload["ctes"]:
        comparison = row.get("comparison") or {}
        rows["CT-e Comparativo"].append(["", row.get("document_number"), row.get("access_key"), comparison.get("gross"), comparison.get("icms")])
    return _package(rows)


def _package(sheets: dict[str, list[list]]) -> bytes:
    buffer = BytesIO()
    names = [name for name, _header in SHEETS]
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types(len(names)))
        archive.writestr("_rels/.rels", _root_rels())
        archive.writestr("xl/workbook.xml", _workbook(names))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(names)))
        archive.writestr("xl/styles.xml", "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"/>")
        for index, name in enumerate(names, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet(sheets[name]))
    return buffer.getvalue()


def _content_types(count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{overrides}</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook(names: list[str]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def _workbook_rels(count: int) -> str:
    rows = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, count + 1)
    )
    styles = f'<Relationship Id="rId{count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rows}{styles}</Relationships>"
    )


def _sheet(rows: list[list]) -> str:
    body = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column, value in enumerate(row, start=1):
            ref = f"{_column(column)}{row_index}"
            text = escape("" if value is None else str(value))
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        body.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(body)}</sheetData></worksheet>'
    )


def _column(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name
