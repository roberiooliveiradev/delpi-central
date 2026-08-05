from __future__ import annotations

import io
import re
from datetime import date, datetime
from html import escape
from typing import Any

import bleach
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from tm_app.application.services.html_sanitizer import TmAtaHtmlSanitizer

_ROLES = {
    "chair": "Condução",
    "secretary": "Secretário(a)",
    "sponsor": "Patrocinador(a)",
    "facilitator": "Facilitador(a)",
    "participant": "Participante",
    "guest": "Convidado(a)",
    "other": "Participante",
}

# Chunks que só têm quebra/espaço (ex.: <p><br></p> do rich-text) — não viram Paragraph.
_EMPTY_CHUNK_RE = re.compile(
    r"^(?:\s|&nbsp;|&#160;|<br\s*/?\s*>)+$",
    re.IGNORECASE,
)


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value or "—")[:10]


def html_to_reportlab_chunks(raw: str | None) -> list[str]:
    """Normaliza HTML do editor para fragmentos seguros no ``Paragraph`` do ReportLab.

    ReportLab usa um subset XHTML: ``<br>`` HTML5 quebra o parser
    (``saw </para> instead of expected </br>``). Espelha a normalização da CIPA.
    """
    text = TmAtaHtmlSanitizer.collapse_nbsp_runs(raw)
    if not (text or "").strip():
        return []
    cleaned = bleach.clean(
        text,
        tags=[
            "p",
            "br",
            "b",
            "strong",
            "i",
            "em",
            "u",
            "ul",
            "ol",
            "li",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        ],
        strip=True,
    )
    # Void <br> → XHTML <br/>
    cleaned = re.sub(r"<\s*br\s*/?\s*>", "<br/>", cleaned, flags=re.IGNORECASE)
    # Tabelas → linhas com células separadas (Paragraph simples não parseia <table>)
    cleaned = re.sub(r"</tr\s*>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</t[dh]\s*>", " | ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?(?:table|thead|tbody|tr|th|td)\b[^>]*>", "", cleaned, flags=re.IGNORECASE)
    # Listas → linhas com marcador (Paragraph simples não parseia <ul>/<li>)
    cleaned = re.sub(r"</?(?:ul|ol)\s*>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<li\b[^>]*>", "• ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</li\s*>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("</p>", "\n").replace("<p>", "")
    cleaned = re.sub(r"</?div\s*>", "\n", cleaned, flags=re.IGNORECASE)
    # strong/em → b/i (mais estável no ReportLab)
    cleaned = re.sub(r"<strong\b[^>]*>", "<b>", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</strong\s*>", "</b>", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<em\b[^>]*>", "<i>", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</em\s*>", "</i>", cleaned, flags=re.IGNORECASE)

    chunks: list[str] = []
    for chunk in cleaned.splitlines():
        piece = chunk.strip()
        if not piece or _EMPTY_CHUNK_RE.match(piece):
            continue
        text_only = re.sub(r"<[^>]+>", "", piece).replace("\xa0", " ").strip()
        if not text_only:
            continue
        chunks.append(piece)
    return chunks


def _paragraphs(raw: str | None, style: ParagraphStyle) -> list[Paragraph]:
    return [Paragraph(chunk, style) for chunk in html_to_reportlab_chunks(raw)]


class MinutePdfRenderer:
    def render(
        self,
        minute: dict[str, Any],
        version: dict[str, Any],
        participants: list[dict[str, Any]],
        signers: list[dict[str, Any]],
        signatures: list[dict[str, Any]],
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=24 * mm,
            rightMargin=24 * mm,
            topMargin=25 * mm,
            bottomMargin=20 * mm,
            title=f"Ata Transforma+ {minute.get('minute_number') or ''}",
            author="Transforma+ Delpi / Transformômetro",
        )
        sample = getSampleStyleSheet()
        title = ParagraphStyle(
            "TmAtaTitle",
            parent=sample["Heading1"],
            alignment=1,
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=8 * mm,
        )
        section = ParagraphStyle(
            "TmAtaSection",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        )
        body = ParagraphStyle(
            "TmAtaBody",
            parent=sample["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=2 * mm,
        )
        story = [
            Paragraph("ATA DE REUNIÃO — TRANSFORMA+", title),
            Paragraph(
                f"<b>Transformômetro</b> · Ata nº {escape(str(minute.get('minute_number') or '—'))} · "
                f"{_date(version.get('meeting_date') or minute.get('meeting_date'))}",
                body,
            ),
        ]
        for label, key in (
            ("Pauta", "agenda_html"),
            ("", "body_html"),
            ("Decisões", "decisions_html"),
            ("Pendências", "pending_html"),
            ("Observações", "observations_html"),
        ):
            blocks = _paragraphs(version.get(key), body)
            if blocks:
                if label:
                    story.append(Paragraph(label, section))
                story.extend(blocks)
        story += [Spacer(1, 4 * mm), Paragraph("Assinaturas", section)]
        signature_by_user = {str(s.get("user_id")): s for s in signatures}
        participant_by_user = {str(p.get("user_id")): p for p in participants}
        rows = []
        for signer in signers:
            signature = signature_by_user.get(str(signer.get("user_id")), {})
            image = signature.get("image_bytes")
            cell: list[Any] = []
            if image:
                cell.append(Image(io.BytesIO(image), width=42 * mm, height=13 * mm))
            else:
                cell.append(Spacer(1, 13 * mm))
            role = participant_by_user.get(str(signer.get("user_id")), {}).get(
                "role_in_meeting", "other"
            )
            cell += [
                Paragraph("______________________________", body),
                Paragraph(
                    escape(
                        str(
                            signature.get("display_name_confirmed")
                            or signer.get("display_name")
                            or "—"
                        )
                    ),
                    body,
                ),
                Paragraph(_ROLES.get(str(role), "Participante"), body),
            ]
            rows.append([cell])
        if rows:
            story.append(
                Table(
                    rows,
                    colWidths=[155 * mm],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                        ]
                    ),
                )
            )
        story += [
            Spacer(1, 4 * mm),
            Paragraph(
                f"Código de validação: {escape(str(minute.get('validation_code') or 'RASCUNHO'))}<br/>"
                f"Hash: {escape(str(version.get('content_hash') or '—'))}",
                ParagraphStyle(
                    "TmAtaMeta",
                    parent=body,
                    fontSize=7,
                    textColor=colors.HexColor("#4b5563"),
                ),
            ),
        ]
        doc.build(story)
        return buffer.getvalue()
