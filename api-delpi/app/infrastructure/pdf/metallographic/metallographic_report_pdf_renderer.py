"""PDF A4 do relatório metalográfico.

A composição segue as seções documentadas do chamado #1400. O HTML original
não está no repositório; este renderer não afirma paridade pixel a pixel.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.domain.engineering.metallographic_report import MEASUREMENT_KEYS

_NAVY = colors.HexColor("#0B3A5B")
_RULE = colors.HexColor("#C5D0D8")
_HEAD = colors.HexColor("#E8EEF3")
_MUTED = colors.HexColor("#5C6B76")
_OK = colors.HexColor("#1B7A3A")
_BAD = colors.HexColor("#9B2C2C")

_MEASUREMENT_ROWS = (
    ("crimp_height_ch", "Altura de crimpagem (CH)", "mm"),
    ("crimp_width_cb", "Largura de crimpagem (CB)", "mm"),
    ("void_area_av", "Porcentagem de vazios (AV)", "%"),
    ("left_burr_gh_e", "Rebarba esquerda (GH-E)", "mm"),
    ("right_burr_gh_d", "Rebarba direita (GH-D)", "mm"),
)

_SAMPLE_ROWS = (
    ("terminal_code", "Código DELPI do terminal"),
    ("terminal_part_number", "Part number do terminal"),
    ("product_harness", "Produto / chicote e revisão"),
    ("cable", "Cabo (código e descrição)"),
    ("conductor_section", "Seção do condutor"),
    ("applicator_tool", "Aplicador / ferramenta"),
    ("press_equipment", "Prensa / equipamento"),
    ("batch_production_order", "Lote ou ordem de produção"),
    ("sample_identification", "Identificação da amostra"),
)


def _escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


class MetallographicReportPdfRenderer:
    def render(self, report: dict[str, Any], images: dict[str, bytes]) -> bytes:
        buffer = BytesIO()
        draft = report.get("status") == "draft"
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Relatório de Análise Metalográfica",
            author="DELPI",
            pageCompression=0,
        )
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "MetTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
        brand = ParagraphStyle(
            "MetBrand",
            parent=title,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#D6E4F0"),
        )
        section = ParagraphStyle(
            "MetSection",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=_NAVY,
            spaceBefore=6,
            spaceAfter=4,
        )
        cell = ParagraphStyle(
            "MetCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1C2830"),
        )
        cell_label = ParagraphStyle(
            "MetLabel",
            parent=cell,
            fontName="Helvetica-Bold",
            textColor=_MUTED,
        )
        story: list[Any] = []
        header = Table(
            [[
                Paragraph("DELPI", brand),
                Paragraph("RELATÓRIO DE ANÁLISE METALOGRÁFICA", title),
            ]],
            colWidths=[28 * mm, 154 * mm],
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(header)
        story.append(Spacer(1, 3 * mm))
        meta = Table(
            [[
                Paragraph(f"<b>Nº</b> {_escape(report.get('report_number'))}", cell),
                Paragraph(f"<b>Data</b> {_escape(report.get('report_date') or '—')}", cell),
                Paragraph(f"<b>Revisão</b> {_escape(report.get('revision'))}", cell),
            ]],
            colWidths=[70 * mm, 56 * mm, 56 * mm],
        )
        meta.setStyle(_grid())
        story.append(meta)
        if draft:
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(
                "RASCUNHO — exportação identificada; não constitui laudo aprovado.",
                ParagraphStyle(
                    "MetDraft",
                    parent=cell,
                    textColor=_BAD,
                    fontName="Helvetica-Bold",
                    alignment=TA_CENTER,
                ),
            ))

        story.append(Paragraph("01 — Identificação da amostra", section))
        sample = report.get("sample") or {}
        sample_rows = [[
            Paragraph(label, cell_label),
            Paragraph(_escape(sample.get(key) or "—"), cell),
        ] for key, label in _SAMPLE_ROWS]
        sample_table = Table(sample_rows, colWidths=[62 * mm, 120 * mm])
        sample_table.setStyle(_grid())
        story.append(sample_table)

        story.append(Paragraph("02 — Análise da seção transversal", section))
        story.append(Table(
            [[
                _image_block(images.get("original"), "Micrografia original", cell),
                _image_block(images.get("measured"), "Micrografia com medições", cell),
            ]],
            colWidths=[91 * mm, 91 * mm],
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("Esquema de referência das cotas", section))
        story.append(_scheme_table(cell))

        story.append(Paragraph("03 — Resultados da medição", section))
        measurements = report.get("measurements") or {}
        rows = [[
            Paragraph("Parâmetro", cell_label),
            Paragraph("Critério / tolerância", cell_label),
            Paragraph("Valor medido", cell_label),
            Paragraph("Unidade", cell_label),
        ]]
        for key, label, unit in _MEASUREMENT_ROWS:
            pair = measurements.get(key) or {}
            rows.append([
                Paragraph(_escape(label), cell),
                Paragraph(_escape(pair.get("criterion") or "—"), cell),
                Paragraph(_escape(pair.get("measured") or "—"), cell),
                Paragraph(unit, cell),
            ])
        measure = Table(rows, colWidths=[62 * mm, 62 * mm, 36 * mm, 22 * mm])
        measure.setStyle(_grid(header=True))
        story.append(measure)
        story.append(Paragraph(
            "A API não calcula conformidade nem inventa limites de engenharia.",
            ParagraphStyle("MetNote", parent=cell, textColor=_MUTED, fontSize=7),
        ))

        story.append(Paragraph("04 — Conclusão técnica", section))
        conclusion = report.get("conclusion") or {}
        result = conclusion.get("result")
        result_label = {
            "conforming": "Conforme",
            "nonconforming": "Não conforme",
        }.get(result, "Não definido")
        result_color = _OK if result == "conforming" else _BAD if result == "nonconforming" else _MUTED
        story.append(Paragraph(
            f"Resultado: <font color='{result_color.hexval()}'><b>{result_label}</b></font>",
            cell,
        ))
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph(
            f"Observações e desvios: {_escape(conclusion.get('notes') or '—')}",
            cell,
        ))

        story.append(Paragraph("05 — Responsável pela análise", section))
        analyst = report.get("analyst") or {}
        story.append(Paragraph(
            f"Nome: {_escape(analyst.get('name') or '—')}",
            cell,
        ))
        story.append(Paragraph(
            "Os resultados referem-se às amostras descritas neste relatório.",
            ParagraphStyle("MetDisc", parent=cell, textColor=_MUTED, fontSize=7, spaceBefore=4),
        ))

        def _page(canvas, doc_):  # noqa: ANN001
            canvas.saveState()
            if draft:
                canvas.setFillColor(colors.Color(0.6, 0.1, 0.1, alpha=0.12))
                canvas.setFont("Helvetica-Bold", 46)
                canvas.translate(A4[0] / 2, A4[1] / 2)
                canvas.rotate(32)
                canvas.drawCentredString(0, 0, "RASCUNHO")
                canvas.rotate(-32)
                canvas.translate(-A4[0] / 2, -A4[1] / 2)
            canvas.setFillColor(_MUTED)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(14 * mm, 8 * mm, "DELPI | RELATÓRIO DE ANÁLISE METALOGRÁFICA")
            canvas.drawRightString(A4[0] - 14 * mm, 8 * mm, f"Página {doc_.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=_page, onLaterPages=_page)
        return buffer.getvalue()


def _grid(*, header: bool = False) -> TableStyle:
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.3, _RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (0, -1), _HEAD) if not header else ("BACKGROUND", (0, 0), (-1, 0), _HEAD),
    ]
    return TableStyle(commands)


def _image_block(content: bytes | None, caption: str, style: ParagraphStyle) -> Table:
    if content:
        flowable = Image(BytesIO(content), width=78 * mm, height=52 * mm, kind="proportional")
    else:
        flowable = Paragraph("Micrografia não anexada", style)
    block = Table(
        [[flowable], [Paragraph(caption, style)]],
        colWidths=[86 * mm],
    )
    block.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.4, _RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return block


def _scheme_table(style: ParagraphStyle) -> Table:
    labels = [
        ["", "CH", ""],
        ["GH-E", "AV", "GH-D"],
        ["", "CB", ""],
    ]
    rows = [[Paragraph(item, style) for item in row] for row in labels]
    table = Table(rows, colWidths=[40 * mm, 40 * mm, 40 * mm], rowHeights=[12 * mm, 16 * mm, 12 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, _NAVY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (1, 1), (1, 1), _HEAD),
    ]))
    return table


def measurement_keys_rendered() -> tuple[str, ...]:
    return MEASUREMENT_KEYS
