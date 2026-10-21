"""PDF A4 do relatório metalográfico.

A página é desenhada nas mesmas coordenadas em milímetros do exportador do
HTML de referência (folha 210×297, origem no canto superior esquerdo).
A marca d'água RASCUNHO permanece apenas para status draft, conforme a
política já vigente da API.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.domain.engineering.metallographic_report import MEASUREMENT_KEYS

_ASSETS = Path(__file__).with_name("assets")
_PAGE_H = A4[1]
_REGULAR = "DelpiSans"
_BOLD = "DelpiSans-Bold"

_NAVY = HexColor("#0b3a5d")
_CYAN = HexColor("#00a4ce")
_INK = HexColor("#25465f")
_MUTED = HexColor("#71899d")
_LINE = HexColor("#cbdbe5")
_LIGHT = HexColor("#f1f6f9")
_ROW = HexColor("#f5f8fa")
_CARD_LINE = HexColor("#d5e2ea")
_META_LINE = HexColor("#d5e3eb")
_IMAGE_LINE = HexColor("#cddde6")
_FRAME = HexColor("#f6f8f9")
_FRAME_LINE = HexColor("#d5e0e6")
_PLACEHOLDER = HexColor("#9aabba")
_PLACEHOLDER_STRONG = HexColor("#0b779f")
_SUB = HexColor("#8197a8")
_RULE = HexColor("#e0e9ee")
_COL_RULE = HexColor("#d7e3e9")
_HEAD_LINE = HexColor("#dce7ed")
_CHECK = HexColor("#8da7b8")
_OBS_LINE = HexColor("#d6e2e9")
_FOOT_MUTED = HexColor("#d5e3ec")

_FIELDS = (
    ("TERMINAL", "terminal_code"),
    ("PART NUMBER DO TERMINAL", "terminal_part_number"),
    ("PRODUTO OU CHICOTE", "product_harness"),
    ("CABO", "cable"),
    ("SEÇÃO DO CONDUTOR", "conductor_section"),
    ("APLICADOR / FERRAMENTA", "applicator_tool"),
    ("PRENSA / EQUIPAMENTO", "press_equipment"),
    ("LOTE / ORDEM DE PRODUÇÃO", "batch_production_order"),
    ("AMOSTRA ANALISADA", "sample_identification"),
)

_ROWS = (
    ("Altura de crimpagem (CH) [mm]", "crimp_height_ch"),
    ("Largura de crimpagem (CB) [mm]", "crimp_width_cb"),
    ("Porcentagem de vazios (AV) [%]", "void_area_av"),
    ("Altura da rebarba esquerda (GH-E) [mm]", "left_burr_gh_e"),
    ("Altura da rebarba direita (GH-D) [mm]", "right_burr_gh_d"),
)

_SECTIONS = (
    (1, "Identificação da amostra", "Preencha os dados do terminal, cabo e processo avaliados.", 33.5),
    (2, "Análise da seção transversal", "Registre a micrografia original e a seção com análise visual.", 78.7),
    (3, "Resultados da medição", "Registre o critério aplicável e o valor obtido para cada característica.", 151.3),
    (4, "Conclusão técnica", "Selecione o resultado final e registre observações ou desvios.", 216.9),
    (5, "Responsável pela análise", "", 264.5),
)


def _register_fonts() -> None:
    if _REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(_REGULAR, str(_ASSETS / "delpi-sans-400.ttf")))
        pdfmetrics.registerFont(TTFont(_BOLD, str(_ASSETS / "delpi-sans-700.ttf")))


def _mark_overflow(line: str) -> str:
    marker = "..."
    if line.endswith(marker):
        return line
    room = max(0, len(line) - len(marker))
    return f"{line[:room].rstrip()}{marker}"


def _safe(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\r", "").replace("–", "-").replace("—", "-").replace("\u00a0", " ").strip()


def _display_date(value: Any) -> str:
    text = _safe(value)
    parts = text.split("-")
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return text


def _revision(value: Any) -> str:
    text = _safe(value)
    return "" if text in {"", "00"} else text


class MetallographicReportPdfRenderer:
    def render(self, report: dict[str, Any], images: dict[str, bytes]) -> bytes:
        _register_fonts()
        buffer = BytesIO()
        drawing = canvas.Canvas(
            buffer,
            pagesize=A4,
            pageCompression=0,
            title="Relatório de Análise Metalográfica",
            author="DELPI",
        )
        self._draw_page(drawing, report, images)
        if report.get("status") == "draft":
            self._draw_draft_mark(drawing)
        drawing.showPage()
        drawing.save()
        return buffer.getvalue()

    def _draw_page(self, drawing: canvas.Canvas, report: dict[str, Any], images: dict[str, bytes]) -> None:
        self._rect(drawing, 0, 0, 210, 1.4, fill=_CYAN)
        self._line(drawing, 0, 28, 210, 28, _HEAD_LINE, 0.6)
        self._image_file(drawing, _ASSETS / "delpi-logo.png", 10, 4.0, 39, 19)
        self._text(drawing, "ANÁLISE METALOGRÁFICA", 56, 7.0, 15.4, _BOLD, _NAVY)
        self._text(drawing, "DE CRIMPAGEM", 56, 12.7, 15.4, _BOLD, _NAVY)
        self._text(drawing, "Avaliação da seção transversal do terminal", 56, 19.7, 8.3, _REGULAR, _MUTED)
        self._card(drawing, 154, 4, 47, 20, fill=_LIGHT, stroke=_META_LINE, radius=2)
        self._text(drawing, "RELATÓRIO Nº", 157, 5.4, 6.2, _BOLD, _MUTED)
        self._fit(drawing, _safe(report.get("report_number")), 157, 8.0, 41, 8.1, _REGULAR, _INK, 6.2)
        self._line(drawing, 157, 12.8, 198.5, 12.8, _LINE, 0.65)
        self._text(drawing, "DATA", 157, 14.0, 6.2, _BOLD, _MUTED)
        self._text(drawing, "REV.", 186, 14.0, 6.2, _BOLD, _MUTED)
        self._fit(drawing, _display_date(report.get("report_date")), 157, 17.0, 25, 7.8, _REGULAR, _INK, 6)
        self._fit(drawing, _revision(report.get("revision")), 186, 17.0, 12, 7.8, _REGULAR, _INK, 6)

        for number, title, subtitle, top in _SECTIONS:
            self._section(drawing, number, title, subtitle, top)

        sample = report.get("sample") or {}
        col_w, gap, grid_y = 62.4, 2.4, 41.1
        for index, (label, key) in enumerate(_FIELDS):
            self._entry(
                drawing,
                label,
                _safe(sample.get(key)),
                9 + (index % 3) * (col_w + gap),
                grid_y + (index // 3) * 11.6,
                col_w,
                10.4,
            )

        slots = (
            ("original", "MICROGRAFIA ORIGINAL", "Imagem óptica sem marcações", "INSERIR MICROGRAFIA", "Selecione a imagem obtida no microscópio", 9),
            ("measured", "SEÇÃO COM MEDIÇÕES", "Área avaliada e dimensões indicadas pelo software", "INSERIR IMAGEM DAS MEDIÇÕES", "Selecione a imagem com áreas e cotas identificadas", 107.25),
        )
        for slot, title, caption, empty, hint, left in slots:
            self._micrograph(drawing, images.get(slot), title, caption, empty, hint, left)

        self._measurements(drawing, report.get("measurements") or {})
        self._image_file(drawing, _ASSETS / "measurement-scheme.png", 128 + 73 * 0.109, 158.9 + 54 * 0.109, 73 * 0.782, 54 * 0.782)
        self._conclusion(drawing, report.get("conclusion") or {})
        self._analyst(drawing, _safe((report.get("analyst") or {}).get("name")))
        self._footer(drawing)

    def _micrograph(
        self,
        drawing: canvas.Canvas,
        content: bytes | None,
        title: str,
        caption: str,
        empty: str,
        hint: str,
        left: float,
    ) -> None:
        width, top, height = 93.75, 86.3, 61
        self._card(drawing, left, top, width, height, fill=white, stroke=_IMAGE_LINE, radius=2.2)
        self._text(drawing, title, left + 2, top + 1.8, 9, _BOLD, _NAVY)
        self._text(drawing, caption, left + 2, top + 5.4, 6.9, _REGULAR, _MUTED)
        frame_x, frame_y, frame_w, frame_h = left + 2, top + 10, width - 4, 50
        self._rect(drawing, frame_x, frame_y, frame_w, frame_h, fill=_FRAME, stroke=_FRAME_LINE, stroke_width=0.7, radius=1.3)
        drawn = self._image_bytes(drawing, content, frame_x + 0.6, frame_y + 0.6, frame_w - 1.2, frame_h - 1.2)
        if not drawn:
            self._center(drawing, empty, frame_x + 1, frame_w - 2, frame_y + frame_h / 2 - 2, 9, _BOLD, _PLACEHOLDER_STRONG)
            self._center(drawing, hint, frame_x + 1, frame_w - 2, frame_y + frame_h / 2 + 2.3, 7, _REGULAR, _MUTED)

    def _measurements(self, drawing: canvas.Canvas, measurements: dict[str, Any]) -> None:
        table_x, table_y, table_w, table_h, head_h = 9, 158.9, 116.8, 54, 8.2
        weights = (1.7, 0.88, 0.88)
        total = sum(weights)
        widths = [((table_w - 0.8) * weight / total) for weight in weights]
        columns = [table_x, table_x + widths[0], table_x + widths[0] + widths[1]]
        row_h = (table_h - head_h) / 5
        self._card(drawing, table_x, table_y, table_w, table_h, fill=white, stroke=HexColor("#ccdce5"), radius=1.8)
        self._rect(drawing, table_x, table_y, table_w, head_h, fill=_NAVY, radius=1.8)
        self._rect(drawing, table_x, table_y + head_h - 1.8, table_w, 1.8, fill=_NAVY)
        self._fit(drawing, "PARÂMETRO", table_x + 1.1, table_y + 3.1, widths[0] - 2.0, 7, _BOLD, white, 6)
        self._fit(drawing, "CRITÉRIO /", columns[1] + 1.1, table_y + 1.5, widths[1] - 2.0, 6.8, _BOLD, white, 5.8)
        self._fit(drawing, "TOLERÂNCIA", columns[1] + 1.1, table_y + 4.7, widths[1] - 2.0, 6.8, _BOLD, white, 5.8)
        self._fit(drawing, "VALOR MEDIDO", columns[2] + 1.1, table_y + 3.1, widths[2] - 2.0, 7, _BOLD, white, 5.8)
        for index, (label, key) in enumerate(_ROWS):
            top = table_y + head_h + index * row_h
            pair = measurements.get(key) or {}
            if index % 2 == 1:
                self._rect(drawing, table_x, top, table_w, row_h, fill=_ROW)
            self._line(drawing, table_x, top, table_x + table_w, top, _RULE, 0.5)
            self._fit(drawing, label, table_x + 1.2, top + (row_h - 3.2) / 2, widths[0] - 2.4, 8.2, _REGULAR, _INK, 7.4)
            self._fit(drawing, _safe(pair.get("criterion")), columns[1] + 1.0, top + max(2.2, (row_h - 3.4) / 2), widths[1] - 2.0, 8.8, _REGULAR, _INK, 6.2)
            self._fit(drawing, _safe(pair.get("measured")), columns[2] + 0.8, top + max(2.2, (row_h - 3.4) / 2), widths[2] - 1.6, 9.2, _REGULAR, _INK, 6.1)
        self._vline(drawing, columns[1], table_y, table_y + table_h, _COL_RULE, 0.5)
        self._vline(drawing, columns[2], table_y, table_y + table_h, _COL_RULE, 0.5)
        self._rect(drawing, table_x, table_y, table_w, table_h, stroke=HexColor("#ccdce5"), stroke_width=0.7, radius=1.8)

    def _conclusion(self, drawing: canvas.Canvas, conclusion: dict[str, Any]) -> None:
        left, top, width, height = 9, 224.5, 192, 36
        self._card(drawing, left, top, width, height, fill=white, stroke=_IMAGE_LINE, radius=1.8)
        self._text(drawing, "RESULTADO GERAL", left + 2.2, top + 1.7, 6.7, _BOLD, _MUTED)
        result = conclusion.get("result")
        self._check(drawing, left + 2.2, top + 5.5, result == "conforming")
        self._text(drawing, "Conforme", left + 7, top + 5.7, 8.4, _BOLD, _INK)
        self._check(drawing, left + 29, top + 5.5, result == "nonconforming")
        self._text(drawing, "Não conforme", left + 33.8, top + 5.7, 8.4, _BOLD, _INK)
        self._text(drawing, "OBSERVAÇÕES / DESVIOS", left + 2.2, top + 12.3, 6.7, _BOLD, _MUTED)
        for index in range(3):
            self._line(drawing, left + 2.2, top + 18.2 + index * 4.7, left + width - 2.2, top + 18.2 + index * 4.7, _OBS_LINE, 0.45)
        wrapped = self._wrap(_safe(conclusion.get("notes")), _REGULAR, 7.6, width - 4.6)
        visible = wrapped[:3]
        if len(wrapped) > 3 and visible:
            visible[-1] = _mark_overflow(visible[-1])
        for index, line in enumerate(visible):
            self._text(drawing, line, left + 2.5, top + 18.8 + index * 4.7, 7.6, _REGULAR, _INK)

    def _analyst(self, drawing: canvas.Canvas, name: str) -> None:
        self._card(drawing, 9, 272.9, 192, 10.7, fill=white, stroke=_CARD_LINE, radius=1.8)
        self._text(drawing, "ANÁLISE REALIZADA POR", 11.2, 274.0, 6.2, _BOLD, _MUTED)
        self._fit(drawing, name, 11.2, 277.3, 187.6, 8.8, _REGULAR, _INK, 6.4)
        self._line(drawing, 11.2, 282.1, 198, 282.1, _LINE, 0.55)

    def _footer(self, drawing: canvas.Canvas) -> None:
        self._rect(drawing, 0, 290, 210, 7, fill=_NAVY)
        self._text(drawing, "DELPI  |  RELATÓRIO DE ANÁLISE METALOGRÁFICA", 10, 291.1, 7, _BOLD, white)
        self._text(drawing, "Resultados referentes às amostras descritas neste documento.", 10, 294.1, 5.9, _REGULAR, _FOOT_MUTED)
        self._text(drawing, "1 / 1", 191, 291.3, 6.3, _BOLD, white)

    def _section(self, drawing: canvas.Canvas, number: int, title: str, subtitle: str, top: float) -> None:
        self._rect(drawing, 9, top, 6.3, 6.3, fill=_NAVY)
        self._center(drawing, f"{number:02d}", 9, 6.3, top + 1.3, 8, _BOLD, white)
        label = title.upper()
        self._text(drawing, label, 17.1, top + 1.0, 11.1, _BOLD, _NAVY)
        if subtitle:
            used = pdfmetrics.stringWidth(label, _BOLD, 11.1) / mm
            self._text(drawing, subtitle, 17.1 + used + 1.7, top + 2.2, 7.2, _REGULAR, _SUB)

    def _entry(self, drawing: canvas.Canvas, label: str, value: str, x: float, y: float, w: float, h: float) -> None:
        self._card(drawing, x, y, w, h, fill=white, stroke=_CARD_LINE, radius=1.8)
        self._text(drawing, label, x + 1.8, y + 1.3, 6.2, _BOLD, _MUTED)
        self._line(drawing, x + 1.8, y + h - 1.2, x + w - 1.8, y + h - 1.2, _LINE, 0.6)
        self._fit(drawing, value, x + 1.8, y + 4.9, w - 3.6, 8.2, _REGULAR, _INK, 6.4)

    def _check(self, drawing: canvas.Canvas, x: float, y: float, selected: bool) -> None:
        self._rect(drawing, x, y, 3.4, 3.4, fill=white, stroke=_CHECK, stroke_width=0.75, radius=0.6)
        if not selected:
            return
        self._line(drawing, x + 0.7, y + 1.8, x + 1.4, y + 2.5, _CYAN, 1.2)
        self._line(drawing, x + 1.4, y + 2.5, x + 2.9, y + 0.7, _CYAN, 1.2)

    def _draw_draft_mark(self, drawing: canvas.Canvas) -> None:
        drawing.saveState()
        drawing.setFillColor(Color(0.6, 0.1, 0.1, alpha=0.12))
        drawing.setFont("Helvetica-Bold", 46)
        drawing.translate(A4[0] / 2, _PAGE_H / 2)
        drawing.rotate(32)
        drawing.drawCentredString(0, 0, "RASCUNHO")
        drawing.restoreState()

    def _card(self, drawing: canvas.Canvas, x: float, y: float, w: float, h: float, **style: Any) -> None:
        drawing.saveState()
        drawing.setFillColor(Color(11 / 255, 58 / 255, 93 / 255, alpha=0.12))
        xpt = x * mm
        ypt = _PAGE_H - (y + h) * mm - 0.35 * mm
        drawing.roundRect(xpt, ypt, w * mm, h * mm, (style.get("radius") or 0) * mm, stroke=0, fill=1)
        drawing.restoreState()
        self._rect(drawing, x, y, w, h, **style)

    def _rect(
        self,
        drawing: canvas.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: Color | None = None,
        stroke: Color | None = None,
        stroke_width: float = 0.7,
        radius: float = 0,
    ) -> None:
        drawing.saveState()
        if fill is not None:
            drawing.setFillColor(fill)
        if stroke is not None:
            drawing.setStrokeColor(stroke)
            drawing.setLineWidth(stroke_width)
        xpt = x * mm
        ypt = _PAGE_H - (y + h) * mm
        if radius:
            drawing.roundRect(xpt, ypt, w * mm, h * mm, radius * mm, stroke=1 if stroke is not None else 0, fill=1 if fill is not None else 0)
        else:
            drawing.rect(xpt, ypt, w * mm, h * mm, stroke=1 if stroke is not None else 0, fill=1 if fill is not None else 0)
        drawing.restoreState()

    def _line(self, drawing: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color: Color, width: float) -> None:
        drawing.saveState()
        drawing.setStrokeColor(color)
        drawing.setLineWidth(width)
        drawing.line(x1 * mm, _PAGE_H - y1 * mm, x2 * mm, _PAGE_H - y2 * mm)
        drawing.restoreState()

    def _vline(self, drawing: canvas.Canvas, x: float, y1: float, y2: float, color: Color, width: float) -> None:
        self._line(drawing, x, y1, x, y2, color, width)

    def _baseline(self, font: str, size: float, top_mm: float) -> float:
        ascent = pdfmetrics.getAscent(font) / 1000 * size
        return _PAGE_H - top_mm * mm - ascent

    def _text(self, drawing: canvas.Canvas, text: str, x: float, top: float, size: float, font: str, color: Color) -> None:
        if not text:
            return
        drawing.setFillColor(color)
        drawing.setFont(font, size)
        drawing.drawString(x * mm, self._baseline(font, size, top), text)

    def _fit(
        self,
        drawing: canvas.Canvas,
        text: str,
        x: float,
        top: float,
        width: float,
        size: float,
        font: str,
        color: Color,
        minimum: float,
    ) -> None:
        if not text:
            return
        current = size
        while current > minimum and pdfmetrics.stringWidth(text, font, current) > width * mm:
            current -= 0.25
        self._text(drawing, text, x, top, current, font, color)

    def _center(self, drawing: canvas.Canvas, text: str, x: float, width: float, top: float, size: float, font: str, color: Color) -> None:
        if not text:
            return
        used = pdfmetrics.stringWidth(text, font, size) / mm
        self._text(drawing, text, x + max(0, (width - used) / 2), top, size, font, color)

    def _wrap(self, text: str, font: str, size: float, width: float) -> list[str]:
        words = [word for word in text.split() if word]
        rows: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if current and pdfmetrics.stringWidth(trial, font, size) > width * mm:
                rows.append(current)
                current = word
            else:
                current = trial
        if current:
            rows.append(current)
        return rows

    def _image_file(self, drawing: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
        self._place_image(drawing, ImageReader(str(path)), x, y, w, h)

    def _image_bytes(self, drawing: canvas.Canvas, content: bytes | None, x: float, y: float, w: float, h: float) -> bool:
        if not content:
            return False
        try:
            reader = ImageReader(BytesIO(content))
            reader.getSize()
        except Exception:
            return False
        self._place_image(drawing, reader, x, y, w, h)
        return True

    def _place_image(self, drawing: canvas.Canvas, reader: ImageReader, x: float, y: float, w: float, h: float) -> None:
        width, height = reader.getSize()
        if width <= 0 or height <= 0:
            return
        scale = min((w * mm) / width, (h * mm) / height)
        drawn_w = width * scale
        drawn_h = height * scale
        xpt = x * mm + (w * mm - drawn_w) / 2
        ypt = _PAGE_H - (y + h) * mm + (h * mm - drawn_h) / 2
        drawing.drawImage(reader, xpt, ypt, drawn_w, drawn_h, mask="auto", preserveAspectRatio=True, anchor="c")


def measurement_keys_rendered() -> tuple[str, ...]:
    return MEASUREMENT_KEYS
