from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _plain(html: str | None) -> str:
    import re

    text = html or ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip() or "—"


class MinutePdfRenderer:
    def render(self, minute: dict[str, Any], version: dict[str, Any], signatures: list[dict[str, Any]]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CipaTitle",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "CipaBody",
            parent=styles["BodyText"],
            alignment=TA_LEFT,
            fontSize=10,
            leading=14,
            spaceAfter=6,
        )
        meta_style = ParagraphStyle(
            "CipaMeta",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )

        unit_label = {"01": "Santa Catarina", "02": "Espírito Santo"}.get(
            minute.get("unit_code"), minute.get("unit_code")
        )
        story: list[Any] = [
            Paragraph("DELPI — Ata da CIPA", title_style),
            Paragraph(
                f"Unidade: {unit_label} · Nº {minute.get('minute_number')} · Versão {version.get('version_number')}",
                meta_style,
            ),
            Spacer(1, 6),
            Paragraph(f"<b>{minute.get('title')}</b>", body_style),
            Paragraph(
                f"Data: {minute.get('meeting_date')} · Local: {minute.get('location') or '—'}",
                body_style,
            ),
            Spacer(1, 8),
            Paragraph("<b>Pauta</b>", body_style),
            Paragraph(_plain(version.get("agenda_html")).replace("\n", "<br/>"), body_style),
            Paragraph("<b>Conteúdo</b>", body_style),
            Paragraph(_plain(version.get("body_html")).replace("\n", "<br/>"), body_style),
            Paragraph("<b>Decisões</b>", body_style),
            Paragraph(_plain(version.get("decisions_html")).replace("\n", "<br/>"), body_style),
            Paragraph("<b>Pendências</b>", body_style),
            Paragraph(_plain(version.get("pending_html")).replace("\n", "<br/>"), body_style),
            Spacer(1, 10),
            Paragraph("<b>Assinaturas</b>", body_style),
        ]

        rows = [["Signatário", "Data/hora", "Hash"]]
        for item in signatures:
            rows.append(
                [
                    str(item.get("display_name_confirmed") or item.get("display_name") or "—"),
                    str(item.get("created_at") or item.get("signed_at") or "—"),
                    str(item.get("content_hash") or "")[:16] + "…",
                ]
            )
        table = Table(rows, colWidths=[70 * mm, 50 * mm, 45 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 10))
        story.append(
            Paragraph(
                f"Código de validação: {minute.get('validation_code') or '—'} · "
                f"Hash do conteúdo: {version.get('content_hash')}",
                meta_style,
            )
        )
        doc.build(story)
        return buffer.getvalue()
