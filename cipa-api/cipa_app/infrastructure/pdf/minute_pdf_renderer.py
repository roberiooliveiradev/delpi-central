from __future__ import annotations

import io
import re
from datetime import date, datetime
from html import escape
from pathlib import Path
from typing import Any

import bleach
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_LOGO_PATH = _ASSETS_DIR / "logo-cipa.png"
_PAGE_WIDTH, _PAGE_HEIGHT = A4
_TEXT = colors.HexColor("#151515")
_MUTED = colors.HexColor("#4b5563")

_MONTHS_PT = (
    "",
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)

_UNIT_LABELS = {
    "01": ("Santa Catarina", "Jaraguá do Sul - SC"),
    "02": ("Espírito Santo", "Espírito Santo"),
}

_ROLE_LABELS = {
    "president": "Presidente da CIPA",
    "vice_president": "Vice-presidente da CIPA",
    "secretary": "Secretário(a) da CIPA",
    "titular_member": "Membro titular",
    "alternate_member": "Membro suplente",
    "guest": "Convidado(a)",
    "action_owner": "Responsável por ação",
    "other": "Participante",
}


def format_date_br(value: Any) -> str:
    parsed = _as_date(value)
    return parsed.strftime("%d/%m/%Y") if parsed else "—"


def format_date_long_pt(value: Any) -> str:
    parsed = _as_date(value)
    if not parsed:
        return "—"
    return f"{parsed.day} de {_MONTHS_PT[parsed.month]} de {parsed.year}"


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value or "").strip()[:10]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _time(value: Any) -> str:
    raw = str(value or "").strip()
    return raw[:5] if raw else "—"


def _safe_inline_html(raw: str) -> str:
    return bleach.clean(
        raw,
        tags=["b", "strong", "i", "em", "u", "br", "a"],
        attributes={"a": ["href"]},
        protocols=["http", "https", "mailto"],
        strip=True,
    )


def html_to_paragraphs(
    raw_html: str | None,
    body_style: ParagraphStyle,
    bullet_style: ParagraphStyle,
) -> list[Flowable]:
    """Converte HTML sanitizado em blocos ReportLab, preservando inline e listas."""
    raw = raw_html or ""
    raw = re.sub(r"<\s*li\b[^>]*>", "\n\n• ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<\s*/\s*li\s*>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(
        r"<\s*/?\s*(?:p|div|h[1-6]|ul|ol)\b[^>]*>",
        "\n\n",
        raw,
        flags=re.IGNORECASE,
    )
    raw = re.sub(r"<\s*br\s*/?\s*>", "<br/>", raw, flags=re.IGNORECASE)
    blocks: list[Flowable] = []
    for part in re.split(r"\n\s*\n", raw):
        cleaned = _safe_inline_html(part.strip())
        if not re.sub(r"<[^>]+>", "", cleaned).strip():
            continue
        is_bullet = cleaned.startswith("• ")
        blocks.append(
            Paragraph(
                cleaned[2:] if is_bullet else cleaned,
                bullet_style if is_bullet else body_style,
                bulletText="•" if is_bullet else None,
            )
        )
    return blocks


def role_label(value: Any) -> str:
    return _ROLE_LABELS.get(str(value or "other"), "Participante")


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
            leftMargin=27 * mm,
            rightMargin=27 * mm,
            topMargin=43 * mm,
            bottomMargin=25 * mm,
            title=f"Ata CIPA {minute.get('minute_number') or ''}",
            author="DELPI — Comissão Interna de Prevenção de Acidentes",
        )
        styles = self._styles()
        story = self._story(minute, version, participants, signers, signatures, styles)

        def decorate(canvas: Canvas, document: SimpleDocTemplate) -> None:
            self._draw_page(canvas, document, minute)

        doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
        return buffer.getvalue()

    def _styles(self) -> dict[str, ParagraphStyle]:
        sample = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "CipaDocumentTitle",
                parent=sample["Heading1"],
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=20,
                textColor=_TEXT,
                spaceAfter=4 * mm,
            ),
            "date": ParagraphStyle(
                "CipaDocumentDate",
                parent=sample["BodyText"],
                alignment=TA_RIGHT,
                fontSize=10,
                leading=14,
                textColor=_TEXT,
                spaceAfter=10 * mm,
            ),
            "body": ParagraphStyle(
                "CipaDocumentBody",
                parent=sample["BodyText"],
                alignment=TA_JUSTIFY,
                fontName="Helvetica",
                fontSize=10.5,
                leading=15,
                textColor=_TEXT,
                spaceAfter=4 * mm,
            ),
            "bullet": ParagraphStyle(
                "CipaDocumentBullet",
                parent=sample["BodyText"],
                alignment=TA_LEFT,
                leftIndent=7 * mm,
                firstLineIndent=-4 * mm,
                bulletIndent=2 * mm,
                fontSize=10.5,
                leading=15,
                textColor=_TEXT,
                spaceAfter=2 * mm,
            ),
            "section": ParagraphStyle(
                "CipaDocumentSection",
                parent=sample["Heading2"],
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=14,
                textColor=_TEXT,
                spaceBefore=3 * mm,
                spaceAfter=3 * mm,
            ),
            "signature_name": ParagraphStyle(
                "CipaSignatureName",
                parent=sample["BodyText"],
                alignment=TA_CENTER,
                fontName="Helvetica-Oblique",
                fontSize=10,
                leading=12,
                textColor=_MUTED,
            ),
            "signature_role": ParagraphStyle(
                "CipaSignatureRole",
                parent=sample["BodyText"],
                alignment=TA_CENTER,
                fontName="Helvetica-Oblique",
                fontSize=9,
                leading=12,
                textColor=_MUTED,
            ),
            "meta": ParagraphStyle(
                "CipaDocumentMeta",
                parent=sample["BodyText"],
                alignment=TA_LEFT,
                fontSize=7.5,
                leading=10,
                textColor=_MUTED,
            ),
        }

    def _story(
        self,
        minute: dict[str, Any],
        version: dict[str, Any],
        participants: list[dict[str, Any]],
        signers: list[dict[str, Any]],
        signatures: list[dict[str, Any]],
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        unit_label, city = _UNIT_LABELS.get(
            str(minute.get("unit_code") or ""),
            (str(minute.get("unit_code") or "DELPI"), str(minute.get("location") or "DELPI")),
        )
        meeting_date = version.get("meeting_date") or minute.get("meeting_date")
        story: list[Flowable] = [
            Paragraph("ATA DE REUNIÃO DA CIPA", styles["title"]),
            Paragraph(f"{escape(city)}, {format_date_long_pt(meeting_date)}.", styles["date"]),
        ]

        if participants:
            names = ", ".join(escape(str(item.get("display_name") or "—")) for item in participants)
            time_text = self._time_sentence(minute)
            intro = (
                f"Aos {format_date_long_pt(meeting_date)}, {time_text}, nas dependências de "
                f"<b>DELPI Conexões Elétricas</b>, realizou-se reunião "
                f"{escape(str(minute.get('meeting_type') or ''))} da Comissão Interna de "
                f"Prevenção de Acidentes e de Assédio — CIPA, com a presença de {names}."
            )
            story.append(Paragraph(intro, styles["body"]))

        sections = [
            ("Pauta", version.get("agenda_html")),
            ("", version.get("body_html")),
            ("Decisões", version.get("decisions_html")),
            ("Pendências", version.get("pending_html")),
            ("Observações", version.get("observations_html")),
        ]
        for title, raw in sections:
            blocks = html_to_paragraphs(raw, styles["body"], styles["bullet"])
            if not blocks:
                continue
            if title:
                story.append(Paragraph(title, styles["section"]))
            story.extend(blocks)

        story.extend(
            [
                Spacer(1, 5 * mm),
                Paragraph(
                    f"<b>DELPI Conexões Elétricas, {format_date_long_pt(meeting_date)}.</b>",
                    styles["body"],
                ),
                Paragraph("Assinaturas:", styles["section"]),
            ]
        )
        story.extend(self._signature_blocks(participants, signers, signatures, styles))
        story.extend(
            [
                Spacer(1, 4 * mm),
                Paragraph(
                    f"Unidade: {escape(unit_label)} · Ata nº "
                    f"{escape(str(minute.get('minute_number') or '—'))} · Versão "
                    f"{escape(str(version.get('version_number') or '—'))}<br/>"
                    f"Código de validação: {escape(str(minute.get('validation_code') or 'RASCUNHO'))}<br/>"
                    f"Hash: {escape(str(version.get('content_hash') or '—'))}",
                    styles["meta"],
                ),
            ]
        )
        return story

    def _time_sentence(self, minute: dict[str, Any]) -> str:
        start = _time(minute.get("start_time"))
        end = _time(minute.get("end_time"))
        location = escape(str(minute.get("location") or "local informado na convocação"))
        if start != "—" and end != "—":
            return f"das {start} às {end}, em {location}"
        if start != "—":
            return f"às {start}, em {location}"
        return f"em {location}"

    def _signature_blocks(
        self,
        participants: list[dict[str, Any]],
        signers: list[dict[str, Any]],
        signatures: list[dict[str, Any]],
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        participant_by_user = {
            str(item.get("user_id")): item for item in participants if item.get("user_id")
        }
        signature_by_user = {
            str(item.get("user_id")): item for item in signatures if item.get("user_id")
        }
        blocks: list[Flowable] = []
        for signer in signers:
            user_id = str(signer.get("user_id") or "")
            participant = participant_by_user.get(user_id, {})
            signature = signature_by_user.get(user_id, {})
            name = str(
                signature.get("display_name_confirmed")
                or signer.get("display_name")
                or participant.get("display_name")
                or "—"
            )
            image_bytes = signature.get("image_bytes")
            content: list[Flowable] = [Spacer(1, 3 * mm)]
            if isinstance(image_bytes, bytes) and image_bytes:
                image = Image(io.BytesIO(image_bytes), width=42 * mm, height=13 * mm)
                image.hAlign = "CENTER"
                content.append(image)
            else:
                content.append(Spacer(1, 13 * mm))
            content.extend(
                [
                    Table(
                        [[""]],
                        colWidths=[132 * mm],
                        rowHeights=[0.5 * mm],
                        style=TableStyle(
                            [("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black)]
                        ),
                    ),
                    Paragraph(escape(name), styles["signature_name"]),
                    Paragraph(
                        escape(role_label(participant.get("role_in_meeting"))),
                        styles["signature_role"],
                    ),
                    Spacer(1, 5 * mm),
                ]
            )
            blocks.append(KeepTogether(content))
        if not signers:
            blocks.append(Paragraph("Nenhum signatário configurado.", styles["body"]))
        return blocks

    def _draw_page(
        self,
        canvas: Canvas,
        document: SimpleDocTemplate,
        minute: dict[str, Any],
    ) -> None:
        canvas.saveState()
        if _LOGO_PATH.is_file():
            logo = ImageReader(str(_LOGO_PATH))
            canvas.drawImage(
                logo,
                22 * mm,
                _PAGE_HEIGHT - 34 * mm,
                width=20 * mm,
                height=20 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            if hasattr(canvas, "setFillAlpha"):
                canvas.setFillAlpha(0.08)
            canvas.drawImage(
                logo,
                (_PAGE_WIDTH - 92 * mm) / 2,
                (_PAGE_HEIGHT - 92 * mm) / 2,
                width=92 * mm,
                height=92 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            if hasattr(canvas, "setFillAlpha"):
                canvas.setFillAlpha(1)

        canvas.setFillColor(_TEXT)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawCentredString(
            _PAGE_WIDTH / 2 + 10 * mm,
            _PAGE_HEIGHT - 18 * mm,
            "COMISSÃO INTERNA DE PREVENÇÃO DE ACIDENTES",
        )
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawCentredString(
            _PAGE_WIDTH / 2 + 10 * mm,
            _PAGE_HEIGHT - 25 * mm,
            "SEGURANÇA: RESPONSABILIDADE DE CADA UM, TAREFA DE TODOS",
        )

        footer_y = 15 * mm
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.7)
        canvas.line(27 * mm, footer_y + 5 * mm, _PAGE_WIDTH - 27 * mm, footer_y + 5 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(29 * mm, footer_y, format_date_br(minute.get("meeting_date")))
        canvas.drawCentredString(_PAGE_WIDTH / 2, footer_y, "DELPI")
        canvas.drawCentredString(
            _PAGE_WIDTH / 2,
            footer_y - 4 * mm,
            _UNIT_LABELS.get(str(minute.get("unit_code") or ""), ("", ""))[1],
        )
        canvas.drawRightString(_PAGE_WIDTH - 29 * mm, footer_y, str(document.page))
        canvas.restoreState()
