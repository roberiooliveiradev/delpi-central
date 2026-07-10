"""Pacote completo de validação de desenho — persistência e reemissão de relatório."""

from __future__ import annotations

import copy
from typing import Any

from app.domain.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


class ChatDrawingValidationPackageService:
    PACKAGE_KEY = "drawingValidationPackage"

    @classmethod
    def strip_for_metadata(cls, package: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(package, dict):
            return {}

        return {
            "drawingAnalysis": package.get("drawingAnalysis"),
            "productSummary": package.get("productSummary"),
            "analyserRoot": package.get("analyserRoot"),
        }

    @classmethod
    def attach_to_payload(cls, payload: dict[str, Any], package: dict[str, Any] | None) -> None:
        stripped = cls.strip_for_metadata(package)

        if stripped.get("drawingAnalysis"):
            payload[cls.PACKAGE_KEY] = stripped

    @classmethod
    def attach_to_metadata(cls, metadata: dict[str, Any], package: dict[str, Any] | None) -> None:
        stripped = cls.strip_for_metadata(package)

        if stripped.get("drawingAnalysis"):
            metadata[cls.PACKAGE_KEY] = stripped

    @classmethod
    def last_from_messages(cls, previous_messages: list | None) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if ChatConversationContextService.message_role(item).lower() != "assistant":
                continue

            metadata = ChatConversationContextService.message_metadata(item)

            if not metadata:
                continue

            package = metadata.get(cls.PACKAGE_KEY)

            if isinstance(package, dict) and package.get("drawingAnalysis"):
                return copy.deepcopy(package)

        return None

    @classmethod
    def last_export_from_messages(cls, previous_messages: list | None) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if ChatConversationContextService.message_role(item).lower() != "assistant":
                continue

            metadata = ChatConversationContextService.message_metadata(item)
            export = metadata.get("drawingAnalysisExport") if isinstance(metadata, dict) else None

            if isinstance(export, dict) and str(export.get("markdown") or "").strip():
                return export

        return None

    @classmethod
    def merge_with_analysis(
        cls,
        package: dict[str, Any],
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        merged = copy.deepcopy(package)
        merged["drawingAnalysis"] = analysis
        return merged

    @classmethod
    def resolve_for_adjustment(
        cls,
        analysis: dict[str, Any],
        *,
        previous_messages: list | None,
    ) -> dict[str, Any]:
        base = cls.last_from_messages(previous_messages)

        if base:
            return cls.merge_with_analysis(base, analysis)

        export = cls.last_export_from_messages(previous_messages)

        return {
            "drawingAnalysis": analysis,
            "productSummary": cls._product_summary_from_analysis(analysis, export),
            "analyserRoot": {},
        }

    @classmethod
    def format_adjusted_report_markdown(
        cls,
        package: dict[str, Any],
        *,
        previous_messages: list | None,
    ) -> str:
        fresh = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

        if cls._package_has_operational_detail(package):
            return fresh

        prior_export = cls.last_export_from_messages(previous_messages)
        prior_markdown = str((prior_export or {}).get("markdown") or "").strip()

        if not cls._markdown_has_operational_detail(prior_markdown):
            return fresh

        return cls._splice_operational_sections(
            prior_markdown=prior_markdown,
            updated_markdown=fresh,
        )

    @classmethod
    def _product_summary_from_analysis(
        cls,
        analysis: dict[str, Any],
        export: dict[str, Any] | None,
    ) -> dict[str, Any]:
        summary = {
            "code": analysis.get("productCode"),
            "description": analysis.get("productDescription"),
            "last_revision_date": analysis.get("revisionApi"),
        }

        tables = (export or {}).get("tables") if isinstance(export, dict) else None

        if not isinstance(tables, list):
            return summary

        for table in tables:
            if not isinstance(table, dict) or table.get("key") != "apiData":
                continue

            rows = table.get("rows") if isinstance(table.get("rows"), list) else []

            for row in rows:
                if not isinstance(row, dict):
                    continue

                field = str(row.get("field") or "").casefold()
                value = str(row.get("value") or "").strip()

                if not value or value == "—":
                    continue

                if "descri" in field:
                    summary["description"] = value
                elif "revis" in field and "api" in field:
                    summary["last_revision_date"] = value
                elif field == "código" or field == "codigo":
                    summary["code"] = value.replace("`", "")

        return summary

    @classmethod
    def _package_has_operational_detail(cls, package: dict[str, Any]) -> bool:
        root = package.get("analyserRoot") if isinstance(package.get("analyserRoot"), dict) else {}

        for key in ("structure", "guide", "inspection"):
            section = root.get(key)

            if not isinstance(section, dict):
                continue

            items = section.get("items")

            if isinstance(items, list) and items:
                return True

        return False

    @classmethod
    def _markdown_has_operational_detail(cls, markdown: str) -> bool:
        structure_marker = cls._section_marker("structure")

        return bool(markdown and structure_marker and structure_marker in markdown)

    @classmethod
    def _section_marker(cls, key: str) -> str:
        return str(
            ChatDrawingValidationContentService.get("report", "sections", key) or ""
        ).strip()

    @classmethod
    def _splice_operational_sections(cls, *, prior_markdown: str, updated_markdown: str) -> str:
        structure_marker = cls._section_marker("structure")
        dimensions_marker = cls._section_marker("dimensions")
        critical_marker = cls._section_marker("critical")

        op_start = prior_markdown.find(structure_marker)

        if op_start < 0:
            return updated_markdown

        op_end_candidates = [
            index
            for index in (
                prior_markdown.find(dimensions_marker, op_start),
                prior_markdown.find(critical_marker, op_start),
            )
            if index >= 0
        ]
        op_end = min(op_end_candidates) if op_end_candidates else len(prior_markdown)
        operational_block = prior_markdown[op_start:op_end].strip()

        insert_at = cls._find_operational_insert_index(updated_markdown)
        tail_start = cls._find_tail_start(updated_markdown, insert_at)

        head = updated_markdown[:insert_at].rstrip()
        tail = updated_markdown[tail_start:].lstrip()

        return "\n\n".join(part for part in (head, operational_block, tail) if part)

    @classmethod
    def _find_operational_insert_index(cls, markdown: str) -> int:
        api_marker = cls._section_marker("apiData")

        api_pos = markdown.find(api_marker)

        if api_pos < 0:
            return len(markdown)

        lines = markdown[api_pos:].splitlines()
        table_started = False
        consumed = 0

        for line in lines:
            consumed += len(line) + 1
            stripped = line.strip()

            if not stripped:
                if table_started:
                    return api_pos + consumed

                continue

            if stripped.startswith("|"):
                table_started = True
                continue

            if table_started:
                return api_pos + consumed - len(line) - 1

        return api_pos + consumed

    @classmethod
    def _find_tail_start(cls, markdown: str, insert_at: int) -> int:
        dimensions_marker = cls._section_marker("dimensions")
        critical_marker = cls._section_marker("critical")
        tail = markdown[insert_at:]

        candidates = [
            tail.find(dimensions_marker),
            tail.find(critical_marker),
        ]
        relative = min(index for index in candidates if index >= 0)

        return insert_at + relative
