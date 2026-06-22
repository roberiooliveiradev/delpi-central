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
from app.domain.services.chat_drawing_analysis_export_consistency_service import (
    ChatDrawingAnalysisExportConsistencyService,
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
        tables = ChatDrawingValidationPresentationService.build_export_tables(package)
        csv_content = cls.build_workbook_csv(tables)
        consistency = ChatDrawingAnalysisExportConsistencyService.validate(
            package=package,
            report_markdown=str(report_markdown or "").strip(),
            export_tables=tables,
        )

        payload: dict[str, Any] = {
            "filename": f"relatorio-desenho-{safe_code}-{stamp}.md",
            "pdfFilename": f"relatorio-desenho-{safe_code}-{stamp}.pdf",
            "xlsxFilename": f"relatorio-desenho-{safe_code}-{stamp}.xlsx",
            "mimeType": "text/markdown; charset=utf-8",
            "markdown": str(report_markdown or "").strip(),
            "statusLabels": ChatDrawingValidationPresentationService.status_labels_map(),
            "exportLabels": {
                "pdfTitle": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfTitle",
                ),
                "pdfSubtitle": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfSubtitle",
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
                "pdfSummaryProduct": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfSummaryProduct",
                ),
                "pdfSummaryStatus": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfSummaryStatus",
                ),
                "pdfSummaryCritical": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfSummaryCritical",
                ),
                "pdfFooterNote": ChatDrawingValidationContentService.get(
                    "export",
                    "pdfFooterNote",
                ),
                "spreadsheetShortHeaders": ChatDrawingValidationContentService.list_values(
                    "export",
                    "spreadsheetShortHeaders",
                ),
            },
        }

        if tables:
            payload["tables"] = tables

        if csv_content.strip():
            payload["csv"] = csv_content
            payload["csvFilename"] = f"relatorio-desenho-{safe_code}-{stamp}.csv"

        nonconformity_rows = cls.build_nonconformity_rows(analysis)

        if nonconformity_rows:
            payload["spreadsheetRows"] = nonconformity_rows

        payload["checklistConsistency"] = consistency

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
    def build_workbook_csv(cls, tables: list[dict[str, Any]]) -> str:
        if not tables:
            return ""

        lines: list[str] = []

        for index, table in enumerate(tables):
            if index > 0:
                lines.append("")

            columns = table.get("columns") if isinstance(table.get("columns"), list) else []
            rows = table.get("rows") if isinstance(table.get("rows"), list) else []
            title = str(table.get("title") or table.get("key") or "").strip()

            if title:
                lines.append(cls._csv_row([title]))

            header = [
                str(column.get("label") or column.get("key") or "")
                for column in columns
                if isinstance(column, dict)
            ]

            if header:
                lines.append(cls._csv_row(header))

            for row in rows:
                if not isinstance(row, dict):
                    continue

                lines.append(
                    cls._csv_row(
                        [
                            str(row.get(str(column.get("key") or "")) or "")
                            for column in columns
                            if isinstance(column, dict)
                        ]
                    )
                )

        body = "\r\n".join(lines)
        return f"sep=;\r\n{body}"

    @classmethod
    def build_nonconformity_csv(cls, analysis: dict[str, Any]) -> str:
        rows = cls.build_nonconformity_rows(analysis)

        if not rows:
            return ""

        header = ChatDrawingValidationPresentationService._export_spreadsheet_headers()
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
