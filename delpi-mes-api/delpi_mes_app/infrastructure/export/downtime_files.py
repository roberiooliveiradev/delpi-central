"""Montagem dos arquivos de exportação gerencial (Etapa 5).

Camada de apresentação de arquivo: recebe fatos/agregados já calculados
pelo owner (Production Control) e serializa CSV, XLSX ou PDF — nunca
recalcula indicadores nem duplica regra de agregação. O bloco de
metadados (filial, filtros, data/hora de extração, fuso e referência de
cálculo) é obrigatório em todo formato (RQ-5.5).
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

CSV_MIME = "text/csv; charset=utf-8"
XLSX_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
PDF_MIME = "application/pdf"

# Colunas canônicas da ocorrência exportada — mesma projeção liberada
# pelo owner via GET /downtimes/export (nenhum campo interno).
_OCCURRENCE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("id", "Identificador"),
    ("workCenter", "Centro de trabalho"),
    ("productionOrder", "Ordem de produção"),
    ("operationCode", "Operação"),
    ("startedAt", "Início"),
    ("endedAt", "Término"),
    ("durationSeconds", "Duração (min)"),
    ("situation", "Situação"),
    ("source", "Origem"),
    ("reasonCode", "Motivo (código)"),
    ("reasonLabel", "Motivo"),
    ("category", "Categoria"),
    ("classification", "Classificação"),
    ("confirmedAt", "Confirmada em"),
    ("confirmedBy", "Confirmada por"),
    ("note", "Observação"),
    ("treatmentStatus", "Triagem"),
    ("treatmentRequest", "Solicitação"),
)

_TREATMENT_STATUS_LABELS = {
    "pending": "Em triagem",
    "referred": "Encaminhada",
    "concluded": "Concluída",
}


def _local(value: str | None, tz: ZoneInfo) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if parsed.tzinfo is None:
        return parsed.strftime("%d/%m/%Y %H:%M:%S")
    return parsed.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")


def _seconds_between(
    started: str | None, ended: str | None, reference: str | None
) -> int | None:
    """Duração da ocorrência — apresentação de campos canônicos: parada
    aberta usa a referenceAt do próprio owner como limite, nunca o relógio
    local do BFF."""
    try:
        start = datetime.fromisoformat((started or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    bound_raw = ended or reference
    try:
        bound = datetime.fromisoformat((bound_raw or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, int((bound - start).total_seconds()))


def _occurrence_row(
    item: dict[str, Any], tz: ZoneInfo, reference_at: str | None
) -> list[Any]:
    seconds = _seconds_between(
        item.get("startedAt"), item.get("endedAt"), reference_at
    )
    confirmed_by = item.get("confirmedByRef") or ""
    treatment_status = item.get("treatmentStatus")
    request_id = item.get("treatmentRequestId") or ""
    cells = {
        "id": item.get("id") or "",
        "workCenter": item.get("workCenter") or "",
        "productionOrder": item.get("productionOrder") or "",
        "operationCode": item.get("operationCode") or "",
        "startedAt": _local(item.get("startedAt"), tz),
        "endedAt": _local(item.get("endedAt"), tz),
        "durationSeconds": (
            round(seconds / 60, 1) if seconds is not None else ""
        ),
        "situation": "Aberta" if not item.get("endedAt") else "Encerrada",
        "source": item.get("source") or "",
        "reasonCode": item.get("reasonCode") or "",
        "reasonLabel": item.get("reasonLabel") or "",
        "category": item.get("category") or "",
        "classification": (
            "Confirmada" if item.get("confirmed") else "Pendente"
        ),
        "confirmedAt": _local(item.get("confirmedAt"), tz),
        "confirmedBy": confirmed_by,
        "note": item.get("note") or "",
        "treatmentStatus": _TREATMENT_STATUS_LABELS.get(
            treatment_status or "", ""
        ),
        "treatmentRequest": request_id,
    }
    return [cells[key] for key, _label in _OCCURRENCE_COLUMNS]


def _metadata_lines(meta: dict[str, Any], tz: ZoneInfo) -> list[str]:
    filters = meta.get("appliedFilters") or {}
    active = {
        key: value for key, value in filters.items() if value not in (None, "", [])
    }
    filters_text = (
        ", ".join(f"{key}={value}" for key, value in active.items())
        if active
        else "nenhum"
    )
    generated = _local(meta.get("generatedAt"), tz)
    reference = _local(meta.get("referenceAt"), tz)
    partial = "sim" if meta.get("capped") else "não"
    return [
        f"# Delpi MES — {meta.get('title', 'Gestão de paradas')}",
        f"# Filial: {meta.get('branch')}",
        f"# Filtros: {filters_text}",
        f"# Extraído em: {generated} ({meta.get('timezone')})",
        f"# Referência de cálculo: {reference}",
        f"# Total de ocorrências: {meta.get('total')}",
        f"# Arquivo parcial (limite de registros): {partial}",
    ]


def build_occurrences_csv(data: dict[str, Any], *, title: str) -> bytes:
    tz = ZoneInfo(data.get("timezone") or "America/Sao_Paulo")
    meta = {**data, "title": title}
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    for line in _metadata_lines(meta, tz):
        writer.writerow([line])
    writer.writerow([])
    writer.writerow([label for _key, label in _OCCURRENCE_COLUMNS])
    for item in data.get("items") or []:
        writer.writerow(
            _occurrence_row(item, tz, data.get("referenceAt"))
        )
    return buffer.getvalue().encode("utf-8-sig")


def build_occurrences_xlsx(data: dict[str, Any], *, title: str) -> bytes:
    from openpyxl import Workbook

    tz = ZoneInfo(data.get("timezone") or "America/Sao_Paulo")
    meta = {**data, "title": title}
    workbook = Workbook()
    info = workbook.active
    info.title = "Metadados"
    for line in _metadata_lines(meta, tz):
        info.append([line.lstrip("# ")])
    sheet = workbook.create_sheet("Paradas")
    sheet.append([label for _key, label in _OCCURRENCE_COLUMNS])
    for item in data.get("items") or []:
        sheet.append(_occurrence_row(item, tz, data.get("referenceAt")))
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_executive_pdf(data: dict[str, Any], *, title: str) -> bytes:
    """PDF executivo — indicadores e Pareto calculados pelo owner
    (mesma consulta analítica do painel); o builder apenas desenha."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import getSampleStyleSheet

    tz = ZoneInfo(data.get("timezone") or "America/Sao_Paulo")
    styles = getSampleStyleSheet()
    blue = colors.HexColor("#013866")
    story: list[Any] = [Paragraph(title, styles["Title"]), Spacer(1, 4 * mm)]

    meta_lines = _metadata_lines({**data, "title": title}, tz)
    story.append(
        Paragraph(
            "<br/>".join(line.lstrip("# ") for line in meta_lines[1:]),
            styles["Small"] if "Small" in styles else styles["Normal"],
        )
    )
    story.append(Spacer(1, 6 * mm))

    summary = data.get("summary") or {}
    def _hours(seconds: Any) -> str:
        try:
            return f"{float(seconds) / 3600:.1f} h"
        except (TypeError, ValueError):
            return "-"

    summary_rows = [
        ["Indicador", "Valor"],
        ["Tempo total parado", _hours(summary.get("totalStoppedSeconds"))],
        ["Tempo atribuído (sem sobreposição)", _hours(summary.get("attributedSeconds"))],
        ["Ocorrências", summary.get("occurrencesCount", "-")],
        ["Duração média", _hours(summary.get("averageOccurrenceSeconds"))],
        ["Pendentes de classificação", summary.get("pendingCount", "-")],
        ["Em aberto", summary.get("openCount", "-")],
    ]
    table = Table(summary_rows, colWidths=[90 * mm, 60 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.extend(
        [Paragraph("Indicadores do período", styles["Heading2"]), table]
    )

    reasons = (data.get("byReason") or [])[:10]
    if reasons:
        top_seconds = max(
            float(reason.get("seconds") or 0) for reason in reasons
        ) or 1.0
        rows = [["Motivo", "Ocorrências", "Tempo", "Participação"]]
        for reason in reasons:
            seconds = float(reason.get("seconds") or 0)
            label = reason.get("label") or reason.get("reasonCode") or "-"
            percent = seconds / top_seconds
            bar = "#" * max(1, int(percent * 30))
            rows.append(
                [
                    label,
                    str(reason.get("occurrencesCount", "-")),
                    _hours(seconds),
                    bar,
                ]
            )
        table = Table(
            rows, colWidths=[70 * mm, 25 * mm, 25 * mm, 55 * mm]
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), blue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("TEXTCOLOR", (3, 1), (3, -1), blue),
                ]
            )
        )
        story.extend(
            [
                Spacer(1, 6 * mm),
                Paragraph("Principais causas (Pareto)", styles["Heading2"]),
                table,
            ]
        )

    centers = (data.get("byWorkCenter") or [])[:10]
    if centers:
        rows = [["Centro de trabalho", "Ocorrências", "Tempo", "% do total"]]
        for center in centers:
            rows.append(
                [
                    center.get("workCenter") or "-",
                    str(center.get("occurrencesCount", "-")),
                    _hours(center.get("seconds")),
                    f"{float(center.get('percentOfTotal') or 0) * 100:.1f}%",
                ]
            )
        table = Table(rows, colWidths=[60 * mm, 30 * mm, 30 * mm, 30 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), blue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )
        story.extend(
            [
                Spacer(1, 6 * mm),
                Paragraph(
                    "Centros de trabalho mais afetados", styles["Heading2"]
                ),
                table,
            ]
        )

    quality = data.get("quality") or {}
    notes: list[str] = []
    if quality.get("overlapDetected"):
        notes.append(
            "Ocorrências sobrepostas detectadas — os totais deduplicados "
            "constam em 'Tempo atribuído'."
        )
    if quality.get("partial") or quality.get("factsCapped"):
        notes.append(
            "Janela parcial: o limite de fatos da consulta foi atingido — "
            "refine os filtros para um relatório completo."
        )
    if notes:
        story.extend(
            [
                Spacer(1, 6 * mm),
                Paragraph("Observações de qualidade", styles["Heading3"]),
            ]
            + [Paragraph("- " + note, styles["Normal"]) for note in notes]
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=title,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )
    doc.build(story)
    return buffer.getvalue()
