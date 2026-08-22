from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from travel_expenses_app.domain.services.pix_key_service import PIX_KEY_TYPE_LABELS

CATEGORY_LABELS = {
    "lodging": "Hospedagem",
    "meals": "Alimentação",
    "fuel": "Combustível",
    "ground_transport": "Deslocamento",
    "air_transport": "Aéreo",
    "toll": "Pedágio",
    "parking": "Estacionamento",
    "communication": "Comunicação",
    "other": "Outros",
}

UNIT_LABELS = {"01": "Santa Catarina", "02": "Espírito Santo"}


def _money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


def _text(value: Any) -> str:
    return str(value or "").strip() or "—"


def _expense_attachment_heading(expense: dict[str, Any], labels: dict[str, str]) -> str:
    category_id = str(expense.get("categoryId") or "other")
    merchant = _text(expense.get("merchant"))
    if merchant == "—":
        merchant = "Sem estabelecimento"
    return (
        f"{_text(expense.get('expenseDate'))} — "
        f"{labels.get(category_id, category_id)} — "
        f"{merchant} — "
        f"{_money(expense.get('amountBrl'))}"
    )


def _append_receipt_attachments(
    story: list,
    expenses: list[dict[str, Any]],
    labels: dict[str, str],
    receipt_attachments: list[dict[str, Any]],
    styles,
) -> None:
    if not receipt_attachments:
        return
    by_receipt_id = {item["receiptId"]: item for item in receipt_attachments}
    expenses_with_receipts = [exp for exp in expenses if exp.get("receipts")]
    if not expenses_with_receipts:
        return

    story.append(Spacer(1, 18))
    story.append(Paragraph("Anexos das despesas", styles["Heading3"]))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Cupons e comprovantes agrupados pela despesa correspondente.",
            styles["Italic"],
        )
    )
    story.append(Spacer(1, 8))

    for expense in expenses_with_receipts:
        story.append(Paragraph(_expense_attachment_heading(expense, labels), styles["Heading4"]))
        story.append(Spacer(1, 4))
        for receipt in expense.get("receipts") or []:
            receipt_id = str(receipt.get("id") or "")
            asset = by_receipt_id.get(receipt_id)
            file_name = _text(receipt.get("originalName") or receipt.get("original_name"))
            mime_type = str(
                (asset or {}).get("mimeType") or receipt.get("mimeType") or receipt.get("mime_type") or ""
            ).lower()
            if asset and asset.get("content") and mime_type.startswith("image/"):
                try:
                    image = RLImage(BytesIO(asset["content"]))
                    max_w, max_h = 170 * mm, 200 * mm
                    scale = min(max_w / image.drawWidth, max_h / image.drawHeight, 1.0)
                    image.drawWidth *= scale
                    image.drawHeight *= scale
                    story.append(image)
                    story.append(Spacer(1, 2))
                except Exception:
                    story.append(Paragraph(f"Anexo: {file_name}", styles["Normal"]))
            else:
                story.append(Paragraph(f"Anexo PDF: {file_name}", styles["Normal"]))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 6))


class TravelPackagePdfRenderer:
    def render(
        self,
        report: dict[str, Any],
        expenses: list[dict[str, Any]],
        categories: list[dict[str, Any]] | None = None,
        receipt_attachments: list[dict[str, Any]] | None = None,
    ) -> bytes:
        labels = {item["id"]: item["label"] for item in (categories or [])}
        labels.update(CATEGORY_LABELS)
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Prestação {report.get('number')}",
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph("DELPI — Despesas de Viagem", styles["Title"]),
            Paragraph(f"Prestação {_text(report.get('number'))}", styles["Heading2"]),
            Spacer(1, 6),
        ]
        meta = [
            ["Viajante", _text(report.get("createdByName") or report.get("createdByEmail"))],
            ["Filial", UNIT_LABELS.get(str(report.get("unitCode")), _text(report.get("unitCode")))],
            ["Destino", _text(report.get("destination"))],
            ["Motivo", _text(report.get("purpose"))],
            ["Período", f"{_text(report.get('periodStart'))} a {_text(report.get('periodEnd'))}"],
            [
                "Centro de custo",
                _text(report.get("costCenterLabel") or report.get("costCenterCode")),
            ],
            ["Total", _money(report.get("totalAmountBrl"))],
        ]
        meta_table = Table(meta, colWidths=[40 * mm, 130 * mm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 12))
        story.append(Paragraph("Despesas", styles["Heading3"]))
        story.append(Spacer(1, 6))

        rows = [["Data", "Categoria", "Estabelecimento", "Valor", "Cupons"]]
        totals: dict[str, float] = {}
        for expense in expenses:
            category_id = str(expense.get("categoryId") or "other")
            amount = float(expense.get("amountBrl") or 0)
            totals[category_id] = totals.get(category_id, 0) + amount
            rows.append(
                [
                    _text(expense.get("expenseDate")),
                    labels.get(category_id, category_id),
                    _text(expense.get("merchant")),
                    _money(amount),
                    str(len(expense.get("receipts") or [])),
                ]
            )
        table = Table(rows, colWidths=[28 * mm, 38 * mm, 55 * mm, 28 * mm, 20 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0, 0.22, 0.4)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.Color(0.8, 0.8, 0.8)),
                    ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 18))
        story.append(Paragraph("Totais por categoria", styles["Heading3"]))
        story.append(Spacer(1, 6))
        cat_rows = [["Categoria", "Total"]]
        for category_id, amount in sorted(totals.items(), key=lambda item: item[0]):
            cat_rows.append([labels.get(category_id, category_id), _money(amount)])
        cat_table = Table(cat_rows, colWidths=[80 * mm, 40 * mm])
        cat_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(cat_table)
        pix_type = str(report.get("pixKeyType") or "").strip()
        pix_value = str(report.get("pixKeyValue") or "").strip()
        if pix_type and pix_value:
            story.append(Spacer(1, 18))
            story.append(Paragraph("PIX para ressarcimento", styles["Heading3"]))
            story.append(Spacer(1, 6))
            pix_label = PIX_KEY_TYPE_LABELS.get(pix_type, pix_type)
            pix_rows = [
                ["Tipo", pix_label],
                ["Chave", pix_value],
            ]
            pix_table = Table(pix_rows, colWidths=[40 * mm, 130 * mm])
            pix_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(pix_table)
        _append_receipt_attachments(
            story,
            expenses,
            labels,
            receipt_attachments or [],
            styles,
        )
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Documento de rascunho — ainda não enviado ao financeiro.",
                styles["Italic"],
            )
        )
        doc.build(story)
        return buffer.getvalue()
