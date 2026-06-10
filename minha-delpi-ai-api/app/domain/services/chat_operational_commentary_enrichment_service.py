"""Enriquecimento canônico pós-tool com dataAnswer + espelho dataCommentary — Playbook 13 P1."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)


class ChatDataInsightEnrichmentService:
    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        data: dict[str, Any] | None = None,
        format_quantity=None,
    ) -> None:
        if not isinstance(metadata, dict) or not isinstance(data, dict):
            return

        data_answer = ChatDataInsightService.build(
            metadata,
            data,
            format_quantity=format_quantity,
        )

        if not data_answer:
            return

        commentary = ChatDataInsightService.build_commentary_mirror(data_answer)

        metadata["dataAnswer"] = data_answer

        if commentary:
            metadata["dataCommentary"] = commentary

        cls._merge_humanized_summary(metadata, commentary or data_answer)
        cls._ensure_text_markdown_commentary(metadata, commentary)
        cls._append_narrative_closing(metadata, commentary)

    @classmethod
    def _merge_humanized_summary(
        cls,
        metadata: dict[str, Any],
        commentary_or_answer: dict[str, Any],
    ) -> None:
        humanized = metadata.get("humanizedSummary")

        if not isinstance(humanized, dict):
            humanized = {}

        existing = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]

        summary_block = commentary_or_answer.get("summary")
        summary = ""

        if isinstance(summary_block, dict):
            summary = str(summary_block.get("answer") or "").strip()
        else:
            summary = str(commentary_or_answer.get("summary") or "").strip()

        commentary_lines = [summary] if summary else []
        commentary_lines.extend(
            str(line).strip()
            for line in (
                commentary_or_answer.get("summaryLines")
                or commentary_or_answer.get("highlights")
                or []
            )
            if str(line or "").strip() and str(line).strip() not in commentary_lines
        )

        merged: list[str] = []

        for line in existing + commentary_lines:
            if line not in merged:
                merged.append(line)

        if merged:
            humanized["linhas"] = merged[:12]

        metadata["humanizedSummary"] = humanized

    @classmethod
    def _ensure_text_markdown_commentary(
        cls,
        metadata: dict[str, Any],
        commentary: dict[str, Any] | None,
    ) -> None:
        if not isinstance(commentary, dict):
            return

        if isinstance(metadata.get("dataAnswer"), dict):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        rendered = ChatOperationalDataCommentaryService.render_markdown_sections(commentary)

        if not rendered:
            return

        if "<!-- section:summary -->" in markdown:
            return

        content_profile = ChatOperationalDataCommentaryService._content_profile(
            str(commentary.get("profileKey") or "factory_status")
        )
        header = ChatOperationalDataCommentaryService._text(
            content_profile,
            "highlightsHeader",
        )

        if header and header in markdown:
            return

        text_presentation["markdown"] = f"{markdown}\n{rendered}".strip()

    @classmethod
    def _append_narrative_closing(
        cls,
        metadata: dict[str, Any],
        commentary: dict[str, Any] | None,
    ) -> None:
        if not isinstance(commentary, dict):
            return

        if isinstance(metadata.get("dataAnswer"), dict):
            return

        insight = str(commentary.get("narrativeInsight") or "").strip()

        if not insight:
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown or insight in markdown:
            return

        from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

        header = ChatAssistantContentService.get(
            "presenter_content",
            "generic",
            "quickReadingHeader",
            default="**Leitura rápida**",
        )

        if header in markdown:
            return

        text_presentation["markdown"] = f"{markdown}\n\n{header}\n\n{insight}".strip()


ChatOperationalCommentaryEnrichmentService = ChatDataInsightEnrichmentService
