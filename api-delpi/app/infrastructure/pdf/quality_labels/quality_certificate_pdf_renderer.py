from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Paleta moderna (alinhada ao design system dos dashboards)
BRAND = colors.HexColor("#013866")
BRAND_SOFT = colors.HexColor("#0EA5E9")
INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#E2E8F0")
ZEBRA = colors.HexColor("#F8FAFC")
HEAD_BG = colors.HexColor("#EFF5FB")
WHITE = colors.white

# Chips de status
OK_BG = colors.HexColor("#E7F6EC")
OK_FG = colors.HexColor("#1B7F3B")
NO_BG = colors.HexColor("#FDE8E8")
NO_FG = colors.HexColor("#C0392B")
NA_BG = colors.HexColor("#EEF1F4")
NA_FG = colors.HexColor("#64748B")

MARGIN = 14 * mm
CONTENT_WIDTH = A4[0] - 2 * MARGIN

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_LOGO = _ASSETS_DIR / "logo_delpi.svg"

SAMPLE_TYPES = (
    ("amostra", "AMOSTRA"),
    ("lote_piloto", "LOTE PILOTO"),
    ("fornecimento", "FORNECIMENTO"),
)

_STATUS_LABEL = {"A": "APROVADO", "R": "REPROVADO", "NA": "N/A"}
_STATUS_COLORS = {
    "A": (OK_BG, OK_FG),
    "R": (NO_BG, NO_FG),
    "NA": (NA_BG, NA_FG),
}


class _DrawingFlowable(Flowable):
    def __init__(self, drawing, width: float, height: float):
        self.drawing = drawing
        self.width = width
        self.height = height

    def wrap(self, _aw: float, _ah: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        from reportlab.graphics import renderPDF

        renderPDF.draw(self.drawing, self.canv, 0, 0)


def _esc(value: Any, empty: str = "") -> str:
    if value is None:
        return empty
    text = str(value).strip()
    return escape(text) if text else empty


class QualityCertificatePdfRenderer:
    """Renderiza o Certificado de Qualidade (RQ-032) em PDF A4 com visual moderno."""

    def render(self, data: dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=16 * mm,
            title="Certificado de Qualidade",
            author="DELPI",
        )
        styles = self._styles()
        story: list[Flowable] = []
        story.append(self._header(data, styles))
        story.append(Spacer(1, 4.5 * mm))
        story.append(self._sample_type_row(data, styles))
        story.append(Spacer(1, 4.5 * mm))
        story.append(self._customer_block(data, styles))
        story.append(Spacer(1, 4.5 * mm))
        story.append(self._checklist(data, styles))
        note = str(data.get("note") or "").strip()
        if note:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(_esc(note), styles["note"]))
        story.append(Spacer(1, 4.5 * mm))
        story.append(self._observations(data, styles))
        story.append(Spacer(1, 2.5 * mm))
        story.append(self._legend(styles))
        doc.build(story)
        return buffer.getvalue()

    # ---------------------------------------------------------------- header

    def _header(self, data: dict[str, Any], styles: dict) -> Flowable:
        logo = self._logo_flowable()
        if logo is None:
            logo = Paragraph('<font color="#013866"><b>Delpi</b></font>', styles["logoFallback"])

        title_cell = [
            Paragraph("CERTIFICADO DE QUALIDADE", styles["docTitle"]),
            Paragraph(_esc(data.get("doc_ref")), styles["docRef"]),
        ]
        header = Table(
            [[logo, title_cell]],
            colWidths=[CONTENT_WIDTH * 0.34, CONTENT_WIDTH * 0.66],
        )
        header.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), WHITE),
                    ("BACKGROUND", (1, 0), (1, 0), BRAND),
                    ("BOX", (0, 0), (0, 0), 1, LINE),
                    ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (0, 0), 12),
                    ("RIGHTPADDING", (0, 0), (0, 0), 12),
                    ("LEFTPADDING", (1, 0), (1, 0), 16),
                    ("RIGHTPADDING", (1, 0), (1, 0), 16),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return header

    # ----------------------------------------------------------- sample type

    def _sample_type_row(self, data: dict[str, Any], styles: dict) -> Flowable:
        selected = str(data.get("sample_type") or "").strip().lower()
        cells: list[Any] = []
        commands: list[tuple] = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]
        gap_cols: list[float] = []
        col_index = 0
        for idx, (key, label) in enumerate(SAMPLE_TYPES):
            is_sel = key == selected
            style_key = "chipOn" if is_sel else "chipOff"
            cells.append(Paragraph(_esc(label), styles[style_key]))
            bg = BRAND if is_sel else HEAD_BG
            commands.append(("BACKGROUND", (col_index, 0), (col_index, 0), bg))
            if not is_sel:
                commands.append(("LINEBELOW", (col_index, 0), (col_index, 0), 0, WHITE))
            gap_cols.append((CONTENT_WIDTH - 2 * 6) / 3)
            col_index += 1
            if idx < len(SAMPLE_TYPES) - 1:
                cells.append("")
                commands.append(("BACKGROUND", (col_index, 0), (col_index, 0), WHITE))
                gap_cols.append(6)
                col_index += 1

        table = Table([cells], colWidths=gap_cols)
        table.setStyle(TableStyle(commands))
        return table

    # -------------------------------------------------------------- customer

    def _customer_block(self, data: dict[str, Any], styles: dict) -> Flowable:
        def kv(label: str, value: Any, empty: str = "—") -> list[Flowable]:
            return [
                Paragraph(_esc(label), styles["kvLabel"]),
                Paragraph(_esc(value, empty), styles["kvValue"]),
            ]

        item_cliente = _esc(data.get("customer_item"), "—")
        rev = str(data.get("customer_item_rev") or "").strip()
        if rev and item_cliente != "—":
            item_cliente = f"{item_cliente} · REV {_esc(rev)}"

        product_op = (
            f"{_esc(data.get('product_code'), '—')}  ·  OP {_esc(data.get('production_order'), '—')}"
        )

        rows = [
            [kv("Cliente", data.get("customer_name")), kv("Item do cliente", item_cliente),
             kv("Quantidade", data.get("quantity"))],
            [kv("Item Delpi / OP", product_op), kv("Quantidade amostral", data.get("sample_quantity")),
             kv("", "")],
        ]
        col = CONTENT_WIDTH / 3.0
        table = Table(rows, colWidths=[col, col, col])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, LINE),
                    ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
                    ("ROUNDEDCORNERS", [8, 8, 8, 8]),
                    ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        return table

    # ------------------------------------------------------------- checklist

    def _checklist(self, data: dict[str, Any], styles: dict) -> Flowable:
        rows: list[list[Any]] = [
            [
                Paragraph("Nº", styles["th"]),
                Paragraph("Item de inspeção", styles["th"]),
                Paragraph("Status", styles["thCenter"]),
            ]
        ]
        commands: list[tuple] = [
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("BOX", (0, 0), (-1, -1), 1, LINE),
            ("LINEBELOW", (0, 0), (-1, 0), 0, BRAND),
            ("INNERGRID", (0, 1), (-1, -1), 0.5, LINE),
            ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 3.8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3.8),
            ("LEFTPADDING", (0, 0), (0, -1), 10),
            ("LEFTPADDING", (1, 0), (1, -1), 12),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]

        items = data.get("items") or []
        for index, item in enumerate(items):
            row_i = index + 1
            status = str(item.get("status") or "").upper()
            if status not in _STATUS_COLORS:
                status = "NA"
            chip_bg, chip_fg = _STATUS_COLORS[status]
            label = _STATUS_LABEL.get(status, "N/A")
            rows.append(
                [
                    Paragraph(_esc(row_i), styles["tdNum"]),
                    Paragraph(_esc(item.get("description")), styles["td"]),
                    Paragraph(
                        f'<font color="#{chip_fg.hexval()[2:]}"><b>{escape(label)}</b></font>',
                        styles["tdCenter"],
                    ),
                ]
            )
            if index % 2 == 1:
                commands.append(("BACKGROUND", (0, row_i), (1, row_i), ZEBRA))
            commands.append(("BACKGROUND", (2, row_i), (2, row_i), chip_bg))

        widths = [14 * mm, CONTENT_WIDTH - 14 * mm - 30 * mm, 30 * mm]
        table = Table(rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle(commands))
        return table

    # ---------------------------------------------------------- observations

    def _observations(self, data: dict[str, Any], styles: dict) -> Flowable:
        signature = self._signature_flowable(data.get("signature_png"))

        delpi_cell: list[Any] = [Paragraph("OBSERVAÇÕES DELPI", styles["obsTitle"])]
        delpi_notes = str(data.get("delpi_notes") or "").strip()
        if delpi_notes:
            delpi_cell.append(Spacer(1, 3 * mm))
            delpi_cell.append(Paragraph(_esc(delpi_notes), styles["obsBody"]))
        delpi_cell.append(Spacer(1, 4 * mm))
        delpi_cell.append(Paragraph("Responsável / Aprovação", styles["obsCaption"]))
        if signature is not None:
            delpi_cell.append(Spacer(1, 1 * mm))
            delpi_cell.append(signature)
        if data.get("inspector_name"):
            delpi_cell.append(Spacer(1, 1 * mm))
            delpi_cell.append(Paragraph(_esc(data.get("inspector_name")), styles["obsName"]))

        customer_cell: list[Any] = [
            Paragraph("OBSERVAÇÕES DO CLIENTE", styles["obsTitle"]),
            Paragraph("(Validação do Projeto)", styles["obsCaption"]),
        ]
        customer_notes = str(data.get("customer_notes") or "").strip()
        if customer_notes:
            customer_cell.append(Spacer(1, 3 * mm))
            customer_cell.append(Paragraph(_esc(customer_notes), styles["obsBody"]))
        customer_cell.append(Spacer(1, 6 * mm))
        customer_cell.append(Paragraph("Responsável / Aprovação", styles["obsCaption"]))

        col = CONTENT_WIDTH / 2.0
        table = Table([[delpi_cell, customer_cell]], colWidths=[col, col])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, LINE),
                    ("LINEAFTER", (0, 0), (0, 0), 0.8, LINE),
                    ("ROUNDEDCORNERS", [8, 8, 8, 8]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ]
            )
        )
        return table

    def _legend(self, styles: dict) -> Flowable:
        return Paragraph(
            '<b>Legenda:</b> APROVADO (conforme) · REPROVADO (não conforme) · '
            "N/A (não aplicável).",
            styles["legend"],
        )

    # ----------------------------------------------------------- flowables

    @staticmethod
    def _signature_flowable(signature_png: bytes | None) -> Flowable | None:
        if not signature_png:
            return None
        try:
            img = Image(BytesIO(signature_png))
            max_w, max_h = 44 * mm, 15 * mm
            ratio = min(max_w / img.imageWidth, max_h / img.imageHeight, 1.0)
            img.drawWidth = img.imageWidth * ratio
            img.drawHeight = img.imageHeight * ratio
            img.hAlign = "LEFT"
            return img
        except Exception:
            return None

    @staticmethod
    def _logo_flowable() -> Flowable | None:
        if not _LOGO.is_file():
            return None
        try:
            from svglib.svglib import svg2rlg

            drawing = svg2rlg(str(_LOGO))
            if drawing is None:
                return None
            max_w, max_h = 44 * mm, 18 * mm
            scale = min(max_w / drawing.width, max_h / drawing.height)
            drawing.width *= scale
            drawing.height *= scale
            drawing.scale(scale, scale)
            return _DrawingFlowable(drawing, drawing.width, drawing.height)
        except Exception:
            return None

    @staticmethod
    def _styles() -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "logoFallback": ParagraphStyle(
                "logoFallback", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=20, textColor=BRAND,
            ),
            "docTitle": ParagraphStyle(
                "docTitle", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=17, leading=20, alignment=TA_LEFT, textColor=WHITE,
            ),
            "docRef": ParagraphStyle(
                "docRef", parent=base["Normal"], fontName="Helvetica",
                fontSize=9, leading=13, alignment=TA_LEFT,
                textColor=colors.HexColor("#BFD4E6"), spaceBefore=3,
            ),
            "chipOn": ParagraphStyle(
                "chipOn", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=WHITE,
            ),
            "chipOff": ParagraphStyle(
                "chipOff", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=MUTED,
            ),
            "kvLabel": ParagraphStyle(
                "kvLabel", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=7, leading=9, textColor=MUTED, spaceAfter=2,
            ),
            "kvValue": ParagraphStyle(
                "kvValue", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=10.5, leading=13, textColor=INK,
            ),
            "th": ParagraphStyle(
                "th", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=8.5, leading=11, alignment=TA_LEFT, textColor=WHITE,
            ),
            "thCenter": ParagraphStyle(
                "thCenter", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=WHITE,
            ),
            "td": ParagraphStyle(
                "td", parent=base["Normal"], fontName="Helvetica",
                fontSize=9, leading=12, textColor=INK,
            ),
            "tdNum": ParagraphStyle(
                "tdNum", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=9, leading=12, alignment=TA_CENTER, textColor=MUTED,
            ),
            "tdCenter": ParagraphStyle(
                "tdCenter", parent=base["Normal"], fontName="Helvetica",
                fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=INK,
            ),
            "note": ParagraphStyle(
                "note", parent=base["Normal"], fontName="Helvetica-Oblique",
                fontSize=9, leading=12, alignment=TA_CENTER, textColor=MUTED,
            ),
            "obsTitle": ParagraphStyle(
                "obsTitle", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=9.5, leading=12, alignment=TA_LEFT, textColor=BRAND,
            ),
            "obsCaption": ParagraphStyle(
                "obsCaption", parent=base["Normal"], fontName="Helvetica",
                fontSize=8, leading=11, alignment=TA_LEFT, textColor=MUTED,
            ),
            "obsBody": ParagraphStyle(
                "obsBody", parent=base["Normal"], fontName="Helvetica",
                fontSize=9, leading=12, alignment=TA_LEFT, textColor=INK,
            ),
            "obsName": ParagraphStyle(
                "obsName", parent=base["Normal"], fontName="Helvetica-Bold",
                fontSize=9.5, leading=12, alignment=TA_LEFT, textColor=INK,
            ),
            "legend": ParagraphStyle(
                "legend", parent=base["Normal"], fontName="Helvetica",
                fontSize=7.5, leading=10, textColor=MUTED,
            ),
        }
