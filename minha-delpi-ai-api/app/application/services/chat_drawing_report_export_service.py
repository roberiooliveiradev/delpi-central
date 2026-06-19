"""Exportação do relatório de análise de desenho — Onda 12.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_presentation_service import (
    ChatDrawingValidationPresentationService,
)


class ChatDrawingReportExportService:
    @classmethod
    def build_export_payload(
        cls,
        *,
        package: dict[str, Any],
        report_markdown: str,
    ) -> dict[str, Any]:
        analysis = package.get("drawingAnalysis") if isinstance(package, dict) else {}
        code = str(analysis.get("productCode") or "desenho").strip()
        safe_code = "".join(char for char in code if char.isalnum()) or "desenho"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        csv_content = cls.build_nonconformity_csv(analysis)

        payload: dict[str, Any] = {
            "filename": f"relatorio-desenho-{safe_code}-{stamp}.md",
            "pdfFilename": f"relatorio-desenho-{safe_code}-{stamp}.pdf",
            "mimeType": "text/markdown; charset=utf-8",
            "markdown": str(report_markdown or "").strip(),
            "statusLabels": ChatDrawingValidationPresentationService.status_labels_map(),
            "exportLabels": {
                "pdfTitle": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfTitle",
                ),
                "nonconformitiesTitle": ChatDrawingValidationContentService.get(
                    "export",
                    "nonconformitiesTitle",
                ),
                "checklistTitle": ChatDrawingValidationContentService.get(
                    "export",
                    "checklistTitle",
                ),
                "criticalCountLabel": ChatDrawingValidationContentService.get(
                    "export",
                    "criticalCountLabel",
                ),
                "spreadsheetShortHeaders": ChatDrawingValidationContentService.list_values(
                    "export",
                    "spreadsheetShortHeaders",
                ),
            },
        }

        if csv_content.strip():
            payload["csv"] = csv_content
            payload["csvFilename"] = f"nao-conformidades-{safe_code}-{stamp}.csv"
            payload["spreadsheetRows"] = cls.build_nonconformity_rows(analysis)

        return payload

    @classmethod
    def build_nonconformity_rows(cls, analysis: dict[str, Any]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        raw_items = analysis.get("items") if isinstance(analysis.get("items"), list) else []
        items = ChatDrawingValidationPresentationService.consolidate_items(raw_items)

        for item in ChatDrawingValidationPresentationService.nonconformity_items(items):
            status = str(item.get("status") or "")

            rows.append(
                {
                    "section": str(item.get("section") or ""),
                    "item": str(item.get("item") or ""),
                    "status": ChatDrawingValidationPresentationService.status_label(status),
                    "pdfEvidence": str(item.get("pdfEvidence") or ""),
                    "apiEvidence": str(item.get("apiEvidence") or ""),
                    "recommendation": str(item.get("recommendation") or ""),
                }
            )

        return rows

    @classmethod
    def build_nonconformity_csv(cls, analysis: dict[str, Any]) -> str:
        rows = cls.build_nonconformity_rows(analysis)

        if not rows:
            return ""

        header = [
            str(cell)
            for cell in ChatDrawingValidationContentService.list_values(
                "export",
                "spreadsheetHeaders",
            )
        ] or [
            "Seção",
            "Item",
            "Status",
            "Evidência PDF",
            "Evidência API",
            "Recomendação",
        ]
        lines = ["\ufeff" + cls._csv_row(header)]

        for row in rows:
            lines.append(
                cls._csv_row(
                    [
                        row["section"],
                        row["item"],
                        row["status"],
                        row["pdfEvidence"],
                        row["apiEvidence"],
                        row["recommendation"],
                    ]
                )
            )

        return "\n".join(lines)

    @classmethod
    def _csv_row(cls, cells: list[str]) -> str:
        escaped: list[str] = []

        for cell in cells:
            text = str(cell or "")

            if ";" in text or '"' in text or "\n" in text:
                text = '"' + text.replace('"', '""') + '"'

            escaped.append(text)

        return ";".join(escaped)

    @classmethod
    def attach_to_metadata(
        cls,
        metadata: dict,
        *,
        package: dict[str, Any] | None,
        report_markdown: str | None,
    ) -> None:
        if not package or not str(report_markdown or "").strip():
            return

        metadata["drawingAnalysisExport"] = cls.build_export_payload(
            package=package,
            report_markdown=str(report_markdown or ""),
        )
