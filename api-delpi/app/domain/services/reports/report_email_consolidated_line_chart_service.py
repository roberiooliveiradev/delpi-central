"""Gráfico de linha PNG (CID) — evolução consolidada em R$ mi para e-mail.

Valores mensais ficam em tabela HTML (legível no Outlook). O PNG mostra só a
tendência (linha + marcadores), com fontes grandes para sobreviver ao downscale.
"""

from __future__ import annotations

import base64
import html
import io
import math
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from app.domain.services.reports.report_email_brand_layout_service import (
    BLUE_900,
    GRAY_200,
    GRAY_600,
    ReportEmailBrandLayoutService,
)
from app.domain.services.reports.report_types import ReportAttachment

CHART_CONTENT_ID = "rol-year-chart"
_BLUE = (1, 56, 102)  # #013866
_BLUE_SOFT = (32, 139, 184)  # #208BB8
_FILL = (1, 56, 102, 48)
_PLOT_BG = (248, 251, 253)
_GRAY_LINE = (148, 163, 184)
_AXIS_TEXT = (30, 41, 59)
_DARK_TEXT = (15, 23, 42)
_WHITE = (255, 255, 255)


class ReportEmailConsolidatedLineChartService:
    """Gera PNG Outlook-safe (anexo CID) + tabela de valores mensais."""

    @staticmethod
    def build(
        *,
        title: str,
        points: Sequence[Mapping[str, Any]],
        series_label: str = "Consolidado",
        year_total_label: str | None = None,
    ) -> tuple[str, ReportAttachment | None]:
        if not points:
            empty = (
                f'<p style="margin:0 0 12px 0;color:{GRAY_600};font-size:13px;">'
                "Sem dados de evolução no período.</p>"
            )
            return empty, None

        png_bytes = ReportEmailConsolidatedLineChartService._render_png(
            points=points,
            series_label=series_label,
        )
        attachment = ReportAttachment(
            name="rol-year-chart.png",
            content_type="image/png",
            content_base64=base64.b64encode(png_bytes).decode("ascii"),
            is_inline=True,
            content_id=CHART_CONTENT_ID,
        )
        safe_title = html.escape(title)
        subtitle = ""
        if year_total_label:
            subtitle = (
                f'<p style="margin:8px 0 0 0;font-size:15px;font-weight:700;'
                f'color:{BLUE_900};font-family:Arial,Helvetica,sans-serif;">'
                f"{html.escape(year_total_label)}</p>"
            )
        values_table = ReportEmailConsolidatedLineChartService._values_table_html(
            points
        )
        card = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'border="0" style="border-collapse:collapse;margin:0 0 20px 0;'
            f'border:1px solid {GRAY_200};border-radius:12px;background:#ffffff;">'
            "<tr><td style=\"padding:16px 16px 8px 16px;\">"
            f'<p style="margin:0;font-size:16px;font-weight:700;color:{BLUE_900};'
            f'font-family:Arial,Helvetica,sans-serif;">{safe_title}</p>'
            f"{subtitle}"
            "</td></tr>"
            '<tr><td style="padding:8px 12px 8px 12px;" align="center">'
            f'<img src="cid:{html.escape(CHART_CONTENT_ID)}" '
            f'alt="{html.escape(series_label)}" width="760" '
            'style="display:block;width:100%;max-width:760px;height:auto;border:0;" />'
            "</td></tr>"
            '<tr><td style="padding:4px 16px 16px 16px;">'
            f'<p style="margin:0 0 8px 0;font-size:12px;font-weight:700;'
            f'color:{BLUE_900};font-family:Arial,Helvetica,sans-serif;">'
            "Valores mensais (R$ mi)</p>"
            f"{values_table}"
            "</td></tr>"
            "</table>"
        )
        return card, attachment

    @staticmethod
    def render_card(
        *,
        title: str,
        points: Sequence[Mapping[str, Any]],
        series_label: str = "Consolidado",
        year_total_label: str | None = None,
    ) -> str:
        html_body, _ = ReportEmailConsolidatedLineChartService.build(
            title=title,
            points=points,
            series_label=series_label,
            year_total_label=year_total_label,
        )
        return html_body

    @staticmethod
    def _values_table_html(points: Sequence[Mapping[str, Any]]) -> str:
        rows = [
            [
                str(point.get("label") or "—"),
                _fmt_mi(float(point.get("value") or 0) / 1_000_000.0, digits=2),
            ]
            for point in points
        ]
        return ReportEmailBrandLayoutService.data_table_html(
            headers=["Mês", "R$ mi"],
            rows=rows,
            column_styles=["text-align:left;", "text-align:right;"],
        )

    @staticmethod
    def _render_png(
        *,
        points: Sequence[Mapping[str, Any]],
        series_label: str,
    ) -> bytes:
        width, height = 1600, 1000
        pad_l, pad_r, pad_t, pad_b = 150, 64, 100, 130
        plot_w = width - pad_l - pad_r
        plot_h = height - pad_t - pad_b

        values_mi = [
            float(point.get("value") or 0) / 1_000_000.0 for point in points
        ]
        labels = [str(point.get("label") or "") for point in points]
        y_min, y_max, step = _axis_bounds(values_mi)

        n = len(values_mi)
        xs = [
            pad_l + (plot_w * (i / (n - 1)) if n > 1 else plot_w / 2)
            for i in range(n)
        ]

        def _y(value: float) -> float:
            span = y_max - y_min if y_max > y_min else 1.0
            return pad_t + plot_h * (1.0 - ((value - y_min) / span))

        image = Image.new("RGBA", (width, height), (*_WHITE, 255))
        draw = ImageDraw.Draw(image, "RGBA")
        # Fontes grandes: o e-mail exibe ~760px de 1600 (~47%).
        font_axis = _load_font(80)
        font_legend = _load_font(64, bold=True)
        font_unit = _load_font(64, bold=True)

        lx, ly = width - 340, 32
        draw.ellipse([(lx, ly), (lx + 28, ly + 28)], fill=(*_BLUE, 255))
        draw.text(
            (lx + 40, ly - 10),
            series_label,
            fill=(*_DARK_TEXT, 255),
            font=font_legend,
        )
        draw.text(
            (pad_l - 8, 34),
            "R$ mi",
            fill=(*_AXIS_TEXT, 255),
            font=font_unit,
        )

        draw.rounded_rectangle(
            [(pad_l - 12, pad_t - 12), (width - pad_r + 12, height - pad_b + 12)],
            radius=20,
            fill=(*_PLOT_BG, 255),
        )

        tick = y_min
        guard = 0
        while tick <= y_max + step * 0.01 and guard < 20:
            guard += 1
            y = _y(tick)
            draw.line(
                [(pad_l, y), (width - pad_r, y)],
                fill=(*_GRAY_LINE, 255),
                width=4,
            )
            label = _fmt_mi(tick, digits=2)
            bbox = draw.textbbox((0, 0), label, font=font_axis)
            tw = bbox[2] - bbox[0]
            draw.text(
                (pad_l - 28 - tw, y - 28),
                label,
                fill=(*_AXIS_TEXT, 255),
                font=font_axis,
            )
            tick = round(tick + step, 10)

        if n >= 2:
            base_y = _y(y_min)
            poly = [(xs[0], base_y)]
            poly.extend((xs[i], _y(values_mi[i])) for i in range(n))
            poly.append((xs[-1], base_y))
            draw.polygon(poly, fill=_FILL)

        for i in range(1, n):
            draw.line(
                [(xs[i - 1], _y(values_mi[i - 1])), (xs[i], _y(values_mi[i]))],
                fill=(*_BLUE, 255),
                width=14,
            )

        for i, value in enumerate(values_mi):
            x, y = xs[i], _y(value)
            r = 22
            draw.ellipse(
                [(x - r - 4, y - r - 4), (x + r + 4, y + r + 4)],
                fill=(*_WHITE, 255),
            )
            draw.ellipse(
                [(x - r, y - r), (x + r, y + r)],
                fill=(*_BLUE, 255),
                outline=(*_BLUE_SOFT, 255),
                width=5,
            )

            xb = draw.textbbox((0, 0), labels[i], font=font_axis)
            lw = xb[2] - xb[0]
            draw.text(
                (x - lw / 2, height - 90),
                labels[i],
                fill=(*_AXIS_TEXT, 255),
                font=font_axis,
            )

        rgb = image.convert("RGB")
        buf = io.BytesIO()
        # Sem optimize=True — prioriza nitidez no Outlook/Gmail.
        rgb.save(buf, format="PNG")
        return buf.getvalue()


def _axis_bounds(values: Sequence[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 3.0, 1.0
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        lo = max(0.0, lo - 1.0)
        hi = lo + 2.0
    span = hi - lo
    pad = max(span * 0.18, 0.25)
    y_min = max(0.0, lo - pad)
    y_max = hi + pad
    raw = (y_max - y_min) / 4.0
    step = _nice_step(raw)
    y_min = math.floor(y_min / step) * step
    y_max = math.ceil(y_max / step) * step
    if y_max <= y_min:
        y_max = y_min + step * 2
    while (y_max - y_min) / step > 7:
        step = _nice_step(step * 1.5)
        y_min = max(0.0, math.floor(lo / step) * step)
        y_max = math.ceil(hi / step) * step
    return round(y_min, 6), round(y_max, 6), step


def _nice_step(raw: float) -> float:
    if raw <= 0:
        return 0.5
    exp = math.floor(math.log10(raw))
    base = raw / (10**exp)
    if base <= 1:
        nice = 1
    elif base <= 2:
        nice = 2
    elif base <= 2.5:
        nice = 2.5
    elif base <= 5:
        nice = 5
    else:
        nice = 10
    return nice * (10**exp)


def _fmt_mi(value: float, *, digits: int = 2) -> str:
    text = f"{value:.{digits}f}".replace(".", ",")
    if digits > 0 and text.endswith("," + ("0" * digits)):
        text = text.split(",")[0]
    return text


def _load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()
