"""Garante paridade checklist `items[]` × markdown × tabelas de export."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_presentation_service import (
    ChatDrawingValidationPresentationService,
)


class ChatDrawingAnalysisExportConsistencyService:
    @classmethod
    def validate(
        cls,
        *,
        package: dict[str, Any],
        report_markdown: str,
        export_tables: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        analysis = package.get("drawingAnalysis") if isinstance(package.get("drawingAnalysis"), dict) else {}
        raw_items = analysis.get("items") if isinstance(analysis.get("items"), list) else []
        display_items = ChatDrawingValidationPresentationService.prepare_display_items(
            raw_items
        )
        display_count = len(display_items)
        markdown_rows = cls._count_markdown_checklist_rows(report_markdown)
        table_rows = cls._count_export_checklist_rows(export_tables or [])
        nonconformity_display = len(
            ChatDrawingValidationPresentationService.nonconformity_items(display_items)
        )
        nonconformity_table = cls._count_export_nonconformity_rows(export_tables or [])
        issues: list[str] = []

        if markdown_rows != display_count:
            issues.append(
                f"markdown_checklist_rows:{markdown_rows}!=display_items:{display_count}"
            )

        if table_rows and table_rows != display_count:
            issues.append(
                f"export_checklist_rows:{table_rows}!=display_items:{display_count}"
            )

        if nonconformity_table and nonconformity_table != nonconformity_display:
            issues.append(
                "export_nonconformity_rows:"
                f"{nonconformity_table}!=display_nonconformities:{nonconformity_display}"
            )

        return {
            "ok": not issues,
            "displayItemCount": display_count,
            "markdownChecklistRows": markdown_rows,
            "exportChecklistRows": table_rows,
            "nonconformityDisplayCount": nonconformity_display,
            "exportNonconformityRows": nonconformity_table,
            "issues": issues,
        }

    @classmethod
    def _count_markdown_checklist_rows(cls, report_markdown: str) -> int:
        text = str(report_markdown or "")
        section_title = str(
            ChatDrawingValidationContentService.get(
                "report",
                "sections",
                "checklist",
                default="## 5. Checklist completo",
            )
        ).strip()

        if not text or not section_title:
            return 0

        lowered = text.casefold()
        marker = section_title.casefold()
        start = lowered.find(marker)

        if start < 0:
            return 0

        block = text[start + len(section_title) :]
        rows = 0
        in_table = False

        for line in block.splitlines():
            stripped = line.strip()

            if not stripped:
                if in_table:
                    break

                continue

            if stripped.startswith("## "):
                if in_table:
                    break

                continue

            if stripped.startswith("|---"):
                in_table = True
                continue

            if stripped.startswith("|") and in_table:
                rows += 1
                continue

            if in_table:
                break

        return rows

    @classmethod
    def _count_export_checklist_rows(cls, tables: list[dict[str, Any]]) -> int:
        for table in tables:
            if not isinstance(table, dict):
                continue

            if str(table.get("key") or "").strip() == "checklist":
                rows = table.get("rows")

                return len(rows) if isinstance(rows, list) else 0

        return 0

    @classmethod
    def _count_export_nonconformity_rows(cls, tables: list[dict[str, Any]]) -> int:
        for table in tables:
            if not isinstance(table, dict):
                continue

            if str(table.get("key") or "").strip() == "nonconformities":
                rows = table.get("rows")

                return len(rows) if isinstance(rows, list) else 0

        return 0
