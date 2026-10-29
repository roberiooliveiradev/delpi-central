"""Tabular A4-landscape PDF renderer for the closing analytical reports.

One renderer for every governed report export (P7/R05/R08): a neutral
spec (title, metadata pairs, table sections, watermark) is drawn with
the same chrome — metadata header, zebra tables with an optional bold
totals row, repeated footer with page numbering and the parity
watermark. The renderer carries no business rule; serializers build
the spec from the SAME payload the query contract returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

_PAGE_W, _PAGE_H = landscape(A4)
_MARGIN = 12 * mm
_HEADER_H = 34 * mm
_FOOTER_H = 12 * mm
_ROW_H = 6.2 * mm
_HEAD_H = 7.2 * mm

_NAVY = HexColor("#0b3a5d")
_INK = HexColor("#25465f")
_MUTED = HexColor("#71899d")
_LINE = HexColor("#cbdbe5")
_LIGHT = HexColor("#f1f6f9")
_ROW = HexColor("#f5f8fa")
_WARN = HexColor("#8a5a00")
_WARN_BG = HexColor("#fdf3e0")


@dataclass(slots=True)
class ReportTableSection:
    title: str
    columns: list[tuple[str, str]]  # (key, header label)
    rows: list[dict[str, Any]]
    totals_row: dict[str, Any] | None = None
    align_right_keys: frozenset[str] = frozenset()


@dataclass(slots=True)
class ClosingReportPdfSpec:
    title: str
    metadata: list[tuple[str, str]]
    sections: list[ReportTableSection] = field(default_factory=list)
    watermark: str | None = None
    footer_note: str = ""


def _text(drawing: canvas.Canvas, text: str, x: float, y: float,
          size: float, color, bold: bool = False) -> None:
    drawing.setFillColor(color)
    drawing.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    drawing.drawString(x, y, text)


def _truncate(text: str, max_chars: int) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _col_widths(
    section: ReportTableSection, usable: float
) -> list[float]:
    """Proportional widths: label column + numeric columns share the
    usable width; numeric cells get roughly uniform weight."""
    weights: list[float] = []
    for key, label in section.columns:
        if key in section.align_right_keys:
            weights.append(1.0)
        else:
            weights.append(max(1.0, len(label) / 14.0))
    total = sum(weights) or 1.0
    return [usable * w / total for w in weights]


def _draw_footer(
    drawing: canvas.Canvas, spec: ClosingReportPdfSpec,
    page: int, total_pages_placeholder: str,
) -> None:
    y = _FOOTER_H - 4 * mm
    drawing.setStrokeColor(_LINE)
    drawing.setLineWidth(0.5)
    drawing.line(_MARGIN, _FOOTER_H, _PAGE_W - _MARGIN, _FOOTER_H)
    note = spec.footer_note or spec.watermark or ""
    _text(drawing, _truncate(note, 150), _MARGIN, y, 6.2, _MUTED)
    _text(
        drawing,
        f"{page}",
        _PAGE_W - _MARGIN - 8 * mm,
        y,
        6.2,
        _MUTED,
        bold=True,
    )


def _draw_header(
    drawing: canvas.Canvas, spec: ClosingReportPdfSpec, stamp: str,
) -> None:
    drawing.setFillColor(_NAVY)
    drawing.rect(0, _PAGE_H - 6 * mm, _PAGE_W, 6 * mm, stroke=0, fill=1)
    _text(
        drawing, spec.title, _MARGIN, _PAGE_H - 16 * mm, 13, _NAVY,
        bold=True,
    )
    _text(
        drawing, stamp, _PAGE_W - _MARGIN - 60 * mm,
        _PAGE_H - 16 * mm, 6.5, _MUTED,
    )
    if spec.watermark:
        drawing.setFillColor(_WARN_BG)
        drawing.rect(
            _MARGIN, _PAGE_H - _HEADER_H + 4 * mm,
            _PAGE_W - 2 * _MARGIN, 7 * mm, stroke=0, fill=1,
        )
        _text(
            drawing,
            _truncate(spec.watermark, 170),
            _MARGIN + 2 * mm,
            _PAGE_H - _HEADER_H + 6 * mm,
            7,
            _WARN,
            bold=True,
        )
    meta_y = _PAGE_H - 25 * mm
    col_w = (_PAGE_W - 2 * _MARGIN) / 4
    for index, (label, value) in enumerate(spec.metadata):
        x = _MARGIN + (index % 4) * col_w
        y = meta_y - (index // 4) * 5.4 * mm
        _text(drawing, f"{label}:", x, y, 6.1, _MUTED, bold=True)
        _text(
            drawing,
            _truncate(str(value), 46),
            x + 22 * mm,
            y,
            6.6,
            _INK,
        )


def _draw_table(
    drawing: canvas.Canvas,
    section: ReportTableSection,
    cursor_y: float,
    spec: ClosingReportPdfSpec,
    page_ref: list[int],
    stamp: str,
) -> float:
    usable = _PAGE_W - 2 * _MARGIN
    widths = _col_widths(section, usable)
    bottom_limit = _FOOTER_H + _ROW_H

    def new_page() -> float:
        drawing.showPage()
        page_ref[0] += 1
        _draw_footer(drawing, spec, page_ref[0], "")
        _draw_header(drawing, spec, stamp)
        return _PAGE_H - _HEADER_H - 8 * mm

    def section_title() -> float:
        nonlocal cursor_y
        if cursor_y < bottom_limit + _HEAD_H + _ROW_H:
            cursor_y = new_page()
        _text(
            drawing, section.title, _MARGIN, cursor_y - 4 * mm, 9,
            _NAVY, bold=True,
        )
        return cursor_y - 8 * mm

    def header_row() -> float:
        nonlocal cursor_y
        drawing.setFillColor(_NAVY)
        drawing.rect(
            _MARGIN, cursor_y - _HEAD_H, usable, _HEAD_H,
            stroke=0, fill=1,
        )
        x = _MARGIN
        for (key, label), width in zip(section.columns, widths):
            _text(
                drawing, _truncate(label.upper(), 34),
                x + 1.4 * mm, cursor_y - _HEAD_H + 2.2 * mm, 6,
                white, bold=True,
            )
            x += width
        return cursor_y - _HEAD_H

    def data_row(row: dict[str, Any], *, zebra: bool, bold: bool) -> float:
        nonlocal cursor_y
        if cursor_y - _ROW_H < bottom_limit:
            cursor_y = new_page()
            cursor_y = header_row()
        if zebra:
            drawing.setFillColor(_ROW)
            drawing.rect(
                _MARGIN, cursor_y - _ROW_H, usable, _ROW_H,
                stroke=0, fill=1,
            )
        drawing.setStrokeColor(_LINE)
        drawing.setLineWidth(0.35)
        drawing.line(
            _MARGIN, cursor_y - _ROW_H,
            _PAGE_W - _MARGIN, cursor_y - _ROW_H,
        )
        x = _MARGIN
        for (key, _label), width in zip(section.columns, widths):
            raw = row.get(key)
            cell = "—" if raw is None else str(raw)
            max_chars = max(int(width / mm * 2.1), 4)
            if key in section.align_right_keys:
                cell_w = drawing.stringWidth(
                    cell, "Helvetica-Bold" if bold else "Helvetica", 6.6
                )
                _text(
                    drawing, _truncate(cell, max_chars),
                    x + width - 1.4 * mm - cell_w,
                    cursor_y - _ROW_H + 1.8 * mm, 6.6, _INK, bold=bold,
                )
            else:
                _text(
                    drawing, _truncate(cell, max_chars),
                    x + 1.4 * mm, cursor_y - _ROW_H + 1.8 * mm, 6.6,
                    _INK, bold=bold,
                )
            x += width
        return cursor_y - _ROW_H

    cursor_y = section_title()
    cursor_y = header_row()
    for index, row in enumerate(section.rows):
        cursor_y = data_row(row, zebra=index % 2 == 1, bold=False)
    if section.totals_row is not None:
        if cursor_y - _ROW_H < bottom_limit:
            cursor_y = new_page()
            cursor_y = header_row()
        drawing.setFillColor(_LIGHT)
        drawing.rect(
            _MARGIN, cursor_y - _ROW_H, usable, _ROW_H,
            stroke=0, fill=1,
        )
        cursor_y = data_row(section.totals_row, zebra=False, bold=True)
    return cursor_y - 4 * mm


def render_closing_report_pdf(
    spec: ClosingReportPdfSpec, *, generated_stamp: str
) -> bytes:
    """Draw the spec into a multi-page A4 landscape PDF and return bytes."""
    buffer = BytesIO()
    drawing = canvas.Canvas(
        buffer,
        pagesize=landscape(A4),
        pageCompression=0,
        title=spec.title,
        author="DELPI",
    )
    page_ref = [1]
    _draw_footer(drawing, spec, page_ref[0], "")
    _draw_header(drawing, spec, generated_stamp)
    cursor_y = _PAGE_H - _HEADER_H - 8 * mm
    for section in spec.sections:
        cursor_y = _draw_table(
            drawing, section, cursor_y, spec, page_ref, generated_stamp
        )
    drawing.showPage()
    drawing.save()
    return buffer.getvalue()
