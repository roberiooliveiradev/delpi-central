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


def _safe_inline_html(raw: str) -> str:
    return bleach.clean(
        raw,
        tags=[
            "b", "strong", "i", "em", "u", "s", "strike", "del",
            "sub", "sup", "br", "a", "font",
        ],
        attributes={
            "a": ["href"],
            "font": ["color", "face", "size", "backcolor"],
        },
        protocols=["http", "https", "mailto"],
        strip=True,
    )


_STYLE_RE = re.compile(
    r"<(span|font)\b([^>]*)style\s*=\s*([\"'])(.*?)\3([^>]*)>(.*?)</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)


def _style_to_reportlab(raw: str) -> tuple[str, str]:
    """Converte CSS do RichTextEditor em tags inline aceitas pelo ReportLab."""
    css: dict[str, str] = {}
    for chunk in raw.split(";"):
        if ":" in chunk:
            key, value = chunk.split(":", 1)
            css[key.strip().lower()] = value.strip()
    opens: list[str] = []
    closes: list[str] = []
    font_attrs: list[str] = []
    if css.get("color"):
        font_attrs.append(f'color="{escape(css["color"])}"')
    background = css.get("background-color") or css.get("background")
    if background:
        font_attrs.append(f'backColor="{escape(background)}"')
    if css.get("font-family"):
        family = css["font-family"].split(",", 1)[0].strip(" \"'")
        family_key = family.lower()
        reportlab_family = (
            "Courier"
            if "courier" in family_key or "monospace" in family_key
            else "Times-Roman"
            if "times" in family_key or "georgia" in family_key or "serif" in family_key
            else "Helvetica"
        )
        font_attrs.append(f'face="{reportlab_family}"')
    if css.get("font-size"):
        match = re.match(r"([\d.]+)(px|pt)?", css["font-size"])
        if match:
            size = float(match.group(1))
            if match.group(2) == "px":
                size *= 0.75
            font_attrs.append(f'size="{size:g}"')
    if font_attrs:
        opens.append(f"<font {' '.join(font_attrs)}>")
        closes.insert(0, "</font>")
    if css.get("font-weight") in {"bold", "bolder", "600", "700", "800", "900"}:
        opens.append("<b>")
        closes.insert(0, "</b>")
    if css.get("font-style") in {"italic", "oblique"}:
        opens.append("<i>")
        closes.insert(0, "</i>")
    decoration = f"{css.get('text-decoration', '')} {css.get('text-decoration-line', '')}"
    if "underline" in decoration:
        opens.append("<u>")
        closes.insert(0, "</u>")
    if "line-through" in decoration:
        opens.append("<strike>")
        closes.insert(0, "</strike>")
    return "".join(opens), "".join(closes)


def _convert_rich_inline(raw: str) -> str:
    # Itera para suportar spans aninhados.
    previous = None
    while raw != previous:
        previous = raw

        def replace(match: re.Match[str]) -> str:
            opening, closing = _style_to_reportlab(match.group(4))
            return f"{opening}{match.group(6)}{closing}"

        raw = _STYLE_RE.sub(replace, raw)
    return raw


def _block_style(
    body_style: ParagraphStyle,
    tag: str,
    attributes: str,
) -> ParagraphStyle:
    style = ParagraphStyle(f"CipaRichText-{tag}", parent=body_style)
    align_match = re.search(
        r"text-align\s*:\s*(left|center|right|justify)",
        attributes,
        re.IGNORECASE,
    )
    if align_match:
        style.alignment = {
            "left": TA_LEFT,
            "center": TA_CENTER,
            "right": TA_RIGHT,
            "justify": TA_JUSTIFY,
        }[align_match.group(1).lower()]
    if tag.startswith("h"):
        level = int(tag[1])
        style.fontName = "Helvetica-Bold"
        style.fontSize = {1: 18, 2: 16, 3: 14, 4: 12, 5: 11, 6: 10}.get(level, 11)
        style.leading = style.fontSize * 1.25
        style.spaceBefore = 3 * mm
        style.spaceAfter = 2 * mm
    if tag == "blockquote":
        style.leftIndent = 10 * mm
        style.rightIndent = 5 * mm
    return style


def html_to_paragraphs(
    raw_html: str | None,
    body_style: ParagraphStyle,
    bullet_style: ParagraphStyle,
) -> list[Flowable]:
    """Converte RichTextEditor HTML em blocos ReportLab preservando formatação."""
    raw = raw_html or ""
    raw = re.sub(r"<\s*br\s*/?\s*>", "<br/>", raw, flags=re.IGNORECASE)
    raw = _convert_rich_inline(raw)

    # Anota cada <li> com o tipo da lista pai para preservar listas mistas.
    def annotate_list(match: re.Match[str]) -> str:
        kind = match.group(1).lower()
        content = re.sub(
            r"<li\b([^>]*)>",
            rf'<li data-list-kind="{kind}"\1>',
            match.group(2),
            flags=re.IGNORECASE,
        )
        return f"<{kind}>{content}</{kind}>"

    raw = re.sub(
        r"<(ol|ul)\b[^>]*>(.*?)</\1\s*>",
        annotate_list,
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    blocks: list[Flowable] = []

    # Cada bloco estrutural recebe seu próprio estilo (heading/alinhamento/recuo).
    block_re = re.compile(
        r"<(p|div|h[1-6]|blockquote|li)\b([^>]*)>(.*?)</\1\s*>",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(block_re.finditer(raw))
    parts: list[tuple[str, str, str]] = []
    if matches:
        for match in matches:
            parts.append((match.group(1).lower(), match.group(2), match.group(3)))
    else:
        parts.append(("p", "", raw))

    ordered_index = 0
    for tag, attributes, content in parts:
        cleaned = _safe_inline_html(content.strip())
        if not re.sub(r"<[^>]+>", "", cleaned).strip():
            continue
        is_bullet = tag == "li"
        is_ordered = is_bullet and 'data-list-kind="ol"' in attributes.lower()
        if is_ordered:
            ordered_index += 1
        bullet_text = f"{ordered_index}." if is_ordered else "•"
        blocks.append(
            Paragraph(
                cleaned,
                bullet_style if is_bullet else _block_style(body_style, tag, attributes),
                bulletText=bullet_text if is_bullet else None,
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
                leftIndent=5 * mm,
                firstLineIndent=-2.5 * mm,
                bulletIndent=1 * mm,
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
