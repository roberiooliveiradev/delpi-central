"""Tabular A4-landscape PDF renderer for the closing analytical reports.

One renderer for every governed report export (P7/R05/R08): a neutral
spec (title, metadata pairs, table sections, watermark) is laid out
with Platypus — Paragraph cells wrap instead of overflowing into the
next column, row height follows the content, table headers repeat on
every page, section titles never orphan and small summary tables stay
together. PT-BR presentation lives here (money, quantities, counts)
driven by serializer-declared key sets; the renderer carries no
business rule — serializers build the spec from the SAME payload the
query contract returns, and internal Decimal precision is preserved
(presentation rounding is display-only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Table,
    TableStyle,
)

_PAGE_W, _PAGE_H = landscape(A4)
_MARGIN = 12 * mm
_HEADER_H = 30 * mm
_FOOTER_H = 12 * mm
_HEAD_ROW_H = 7.2 * mm

# Small tables (summaries) are never split mid-way — a lone summary row
# orphaned on the next page was a reported defect.
_KEEP_TOGETHER_MAX_ROWS = 24
# Space needed before a section starts: title + header + two rows —
# otherwise the section opens on the next page (no orphan headers).
_SECTION_MIN_SPACE = 30 * mm
# A single cell never spans more than this — pathological values would
# otherwise produce a row taller than the page (unrenderable). The
# marker makes the truncation explicit, never silent.
_CELL_CHAR_CAP = 1000

_NAVY = HexColor("#0b3a5d")
_INK = HexColor("#25465f")
_MUTED = HexColor("#71899d")
_LINE = HexColor("#cbdbe5")
_LIGHT = HexColor("#f1f6f9")
_ROW = HexColor("#f5f8fa")
_WARN = HexColor("#8a5a00")
_WARN_BG = HexColor("#fdf3e0")

_CELL = ParagraphStyle(
    "cell", fontName="Helvetica", fontSize=6.6, leading=8.0,
    textColor=_INK,
)
_CELL_BOLD = ParagraphStyle(
    "cell-bold", parent=_CELL, fontName="Helvetica-Bold",
)
_CELL_RIGHT = ParagraphStyle("cell-right", parent=_CELL, alignment=2)
_CELL_BOLD_RIGHT = ParagraphStyle(
    "cell-bold-right", parent=_CELL_BOLD, alignment=2,
)
_HEAD = ParagraphStyle(
    "head", fontName="Helvetica-Bold", fontSize=6.0, leading=7.2,
    textColor=white,
)
_HEAD_RIGHT = ParagraphStyle("head-right", parent=_HEAD, alignment=2)
_SECTION = ParagraphStyle(
    "section", fontName="Helvetica-Bold", fontSize=9, leading=11,
    textColor=_NAVY, spaceAfter=2.5 * mm,
)
_NOTE = ParagraphStyle(
    "note", fontName="Helvetica", fontSize=6.4, leading=8.0,
    textColor=_MUTED, spaceBefore=1.6 * mm, spaceAfter=3 * mm,
)
_META_LABEL = ParagraphStyle(
    "meta-label", fontName="Helvetica-Bold", fontSize=6.1, leading=7.6,
    textColor=_MUTED,
)
_META_VALUE = ParagraphStyle(
    "meta-value", fontName="Helvetica", fontSize=6.6, leading=7.8,
    textColor=_INK,
)
_POLICY = ParagraphStyle(
    "policy", fontName="Helvetica-Oblique", fontSize=6.4, leading=8.0,
    textColor=_MUTED, spaceAfter=2 * mm,
)


@dataclass(slots=True)
class ReportTableSection:
    title: str
    columns: list[tuple[str, str]]  # (key, header label)
    rows: list[dict[str, Any]]
    totals_row: dict[str, Any] | None = None
    align_right_keys: frozenset[str] = frozenset()
    # PT-BR presentation keys: money renders `R$ 14.638.712,48`;
    # quantity renders pt-BR decimals (min 2, max 4). Keys absent from
    # every set are drawn verbatim — codes and counts are never
    # re-formatted.
    money_keys: frozenset[str] = frozenset()
    quantity_keys: frozenset[str] = frozenset()
    # Muted explanatory line rendered under the table (e.g. the
    # monetary-presentation policy or the SB9 × composed-total
    # distinction).
    note: str | None = None
    # Force the whole section onto one page when it fits — used for
    # small summary tables whose rows must not scatter.
    keep_together: bool = False


@dataclass(slots=True)
class ClosingReportPdfSpec:
    title: str
    metadata: list[tuple[str, str]]
    sections: list[ReportTableSection] = field(default_factory=list)
    watermark: str | None = None
    footer_note: str = ""
    # Monetary/display policy note rendered once under the metadata
    # block on the first page.
    policy_note: str | None = None


# ---------- PT-BR presentation ------------------------------------------

def _pt_br_decimal(value: Decimal, decimals: int) -> str:
    """Format a Decimal pt-BR (`.` thousands, `,` decimals) — display
    only; the quantized value never feeds any total."""
    quantum = Decimal(1).scaleb(-decimals)
    rounded = abs(value).quantize(quantum, rounding=ROUND_HALF_UP)
    int_part, _, frac = f"{rounded:f}".partition(".")
    groups: list[str] = []
    while len(int_part) > 3:
        groups.append(int_part[-3:])
        int_part = int_part[:-3]
    groups.append(int_part)
    formatted = ".".join(reversed(groups))
    if decimals:
        formatted += "," + frac.ljust(decimals, "0")[:decimals]
    return ("-" if value < 0 else "") + formatted


def format_money_pt_br(raw: Any) -> str:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return "—" if raw is None else str(raw)
    return "R$ " + _pt_br_decimal(value, 2)


def format_quantity_pt_br(raw: Any) -> str:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return "—" if raw is None else str(raw)
    formatted = _pt_br_decimal(value, 4)
    integer, sep, frac = formatted.rpartition(",")
    if not sep:
        return formatted + ",00"
    return f"{integer},{frac.rstrip('0').ljust(2, '0')}"


def _cell_text(section: ReportTableSection, key: str, raw: Any) -> str:
    if raw is None:
        return "—"
    if key in section.money_keys:
        return format_money_pt_br(raw)
    if key in section.quantity_keys:
        return format_quantity_pt_br(raw)
    text = str(raw).replace("\n", " ").strip()
    if len(text) > _CELL_CHAR_CAP:
        return text[: _CELL_CHAR_CAP - 25] + "… [conteúdo truncado]"
    return text


# ---------- page chrome ---------------------------------------------------

def _draw_chrome(
    drawing: canvas.Canvas,
    spec: ClosingReportPdfSpec,
    stamp: str,
    doc: BaseDocTemplate,
) -> None:
    """Repeated header/footer — compact identification, parity strip."""
    drawing.setFillColor(_NAVY)
    drawing.rect(0, _PAGE_H - 6 * mm, _PAGE_W, 6 * mm, stroke=0, fill=1)
    drawing.setFillColor(_NAVY)
    drawing.setFont("Helvetica-Bold", 12.5)
    drawing.drawString(_MARGIN, _PAGE_H - 15 * mm, spec.title)
    drawing.setFillColor(_MUTED)
    drawing.setFont("Helvetica", 6.8)
    drawing.drawRightString(
        _PAGE_W - _MARGIN, _PAGE_H - 15 * mm, f"Emitido em {stamp}"
    )
    if spec.watermark:
        drawing.setFillColor(_WARN_BG)
        drawing.rect(
            _MARGIN, _PAGE_H - _HEADER_H + 4 * mm,
            _PAGE_W - 2 * _MARGIN, 7 * mm, stroke=0, fill=1,
        )
        drawing.setFillColor(_WARN)
        drawing.setFont("Helvetica-Bold", 7)
        drawing.drawString(
            _MARGIN + 2 * mm, _PAGE_H - _HEADER_H + 6.4 * mm,
            spec.watermark[:170],
        )
    drawing.setStrokeColor(_LINE)
    drawing.setLineWidth(0.5)
    drawing.line(_MARGIN, _FOOTER_H, _PAGE_W - _MARGIN, _FOOTER_H)
    drawing.setFillColor(_MUTED)
    drawing.setFont("Helvetica", 6.2)
    note = spec.footer_note or spec.title
    drawing.drawString(_MARGIN, _FOOTER_H - 4 * mm, note[:140])


class _NumberedCanvas(canvas.Canvas):
    """Two-pass canvas: writes `Página X de Y` once the total is known."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.pop("pageCompression", None)
        super().__init__(*args, pageCompression=0, **kwargs)
        self._saved: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont("Helvetica-Bold", 6.2)
            self.setFillColor(_MUTED)
            self.drawRightString(
                _PAGE_W - _MARGIN,
                _FOOTER_H - 4 * mm,
                f"Página {self._pageNumber} de {total}",
            )
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


# ---------- layout --------------------------------------------------------

def _column_widths(
    section: ReportTableSection, cells: list[list[str]], usable: float
) -> list[float]:
    """Numeric columns take the width their formatted content needs;
    the remaining space is shared by text columns weighted by their
    natural width — descriptions grow, narrow codes do not."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    right = (
        section.align_right_keys
        | section.money_keys
        | section.quantity_keys
    )
    pad = 2.8 * mm
    widths = [0.0] * len(section.columns)
    flex: list[int] = []
    for index, (key, label) in enumerate(section.columns):
        natural = stringWidth(label.upper(), "Helvetica-Bold", 6.0)
        for row in cells:
            natural = max(
                natural,
                stringWidth(row[index], "Helvetica", 6.6),
            )
        natural += pad
        if key in right:
            widths[index] = min(max(natural, 13 * mm), 42 * mm)
        else:
            flex.append(index)
            widths[index] = min(natural, 60 * mm)
    fixed = sum(w for i, w in enumerate(widths) if i not in flex)
    natural_flex = sum(widths[i] for i in flex)
    remaining = usable - fixed
    if not flex:
        # All-numeric table: stretch the widest columns evenly.
        if widths and fixed < usable:
            extra = (usable - fixed) / len(widths)
            widths = [w + extra for w in widths]
        return widths
    if natural_flex <= 0:
        share = max(remaining / len(flex), 12 * mm)
        for i in flex:
            widths[i] = share
    elif natural_flex < remaining:
        for i in flex:
            widths[i] += widths[i] / natural_flex * (remaining - natural_flex)
    else:
        for i in flex:
            widths[i] = max(widths[i] / natural_flex * remaining, 11 * mm)
    return widths


def _table_flowable(
    section: ReportTableSection, usable: float
) -> Table | Paragraph:
    if not section.rows and section.totals_row is None:
        return Paragraph("Sem registros para os filtros aplicados.", _NOTE)

    right = (
        section.align_right_keys
        | section.money_keys
        | section.quantity_keys
    )
    header = [
        Paragraph(label.upper(), _HEAD_RIGHT if key in right else _HEAD)
        for key, label in section.columns
    ]
    cells = [
        [
            _cell_text(section, key, row.get(key))
            for key, _label in section.columns
        ]
        for row in section.rows
    ]
    data = [header]
    for row_texts in cells:
        data.append(
            [
                Paragraph(
                    text,
                    _CELL_RIGHT if key in right else _CELL,
                )
                for text, (key, _label) in zip(row_texts, section.columns)
            ]
        )
    totals_index: int | None = None
    if section.totals_row is not None:
        totals_index = len(data)
        data.append(
            [
                Paragraph(
                    _cell_text(section, key, section.totals_row.get(key)),
                    _CELL_BOLD_RIGHT if key in right else _CELL_BOLD,
                )
                for key, _label in section.columns
            ]
        )

    widths = _column_widths(section, cells, usable)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.4 * mm),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, _NAVY),
        ("GRID", (0, 1), (-1, -1), 0.35, _LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for index in range(1, len(data)):
        target = totals_index if index == totals_index else index
        if index == totals_index:
            style.append(
                ("BACKGROUND", (0, target), (-1, target), _LIGHT)
            )
            style.append(
                ("LINEABOVE", (0, target), (-1, target), 0.6, _NAVY)
            )
        elif index % 2 == 0:
            style.append(("BACKGROUND", (0, index), (-1, index), _ROW))
    return Table(
        data,
        colWidths=widths,
        repeatRows=1,
        style=TableStyle(style),
        hAlign="LEFT",
    )


def _metadata_table(
    spec: ClosingReportPdfSpec, usable: float
) -> Table:
    pairs = list(spec.metadata)
    col_pairs = 3
    label_w = 26 * mm
    value_w = (usable - col_pairs * label_w) / col_pairs
    rows: list[list[Any]] = []
    for start in range(0, len(pairs), col_pairs):
        row: list[Any] = []
        for label, value in pairs[start : start + col_pairs]:
            row.append(Paragraph(f"{label}:", _META_LABEL))
            row.append(Paragraph(str(value), _META_VALUE))
        while len(row) < col_pairs * 2:
            row.append(Paragraph("", _META_VALUE))
        rows.append(row)
    return Table(
        rows,
        colWidths=[label_w, value_w] * col_pairs,
        style=TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 0.8 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, _LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        ),
        hAlign="LEFT",
    )


def render_closing_report_pdf(
    spec: ClosingReportPdfSpec, *, generated_stamp: str
) -> bytes:
    """Lay the spec out as a multi-page A4 landscape PDF — headers and
    page numbers repeat on every page, cells wrap and never overlap."""
    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_HEADER_H + 2 * mm,
        bottomMargin=_FOOTER_H + 3 * mm,
        title=spec.title,
        author="DELPI",
        subject=spec.footer_note or spec.title,
        creator="Minha DELPI — Portal Controladoria",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(
                id="report",
                frames=[frame],
                onPage=lambda d, ddoc: _draw_chrome(d, spec, generated_stamp, ddoc),
            )
        ]
    )

    usable = doc.width
    story: list[Any] = [_metadata_table(spec, usable)]
    if spec.policy_note:
        story.append(Paragraph(spec.policy_note, _POLICY))

    for section in spec.sections:
        story.append(CondPageBreak(_SECTION_MIN_SPACE))
        block: list[Any] = [
            Paragraph(section.title, _SECTION),
            _table_flowable(section, usable),
        ]
        if section.note:
            block.append(Paragraph(section.note, _NOTE))
        if section.keep_together or (
            len(section.rows) <= _KEEP_TOGETHER_MAX_ROWS
            and section.totals_row is not None
        ):
            story.append(KeepTogether(block))
        else:
            story.extend(block)
    doc.build(story, canvasmaker=_NumberedCanvas)
    return buffer.getvalue()
