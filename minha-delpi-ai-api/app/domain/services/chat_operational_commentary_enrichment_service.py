"""Liga comentário operacional ao metadata do turno e ao contexto do LLM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)


class ChatOperationalCommentaryEnrichmentService:
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

        profile_key = ChatOperationalDataCommentaryService.resolve_profile_key(
            path=str(metadata.get("path") or ""),
            metadata=metadata,
        )

        if not profile_key:
            return

        commentary = ChatOperationalDataCommentaryService.build(
            profile_key,
            data,
            format_quantity=format_quantity,
        )

        if not commentary:
            return

        metadata["dataCommentary"] = commentary
        cls._merge_humanized_summary(metadata, commentary)
        cls._ensure_text_markdown_commentary(metadata, commentary)
        cls._append_narrative_closing(metadata, commentary)

    @classmethod
    def _merge_humanized_summary(
        cls,
        metadata: dict[str, Any],
        commentary: dict[str, Any],
    ) -> None:
        humanized = metadata.get("humanizedSummary")

        if not isinstance(humanized, dict):
            humanized = {}

        existing = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]
        commentary_lines = [
            str(line).strip()
            for line in (commentary.get("summaryLines") or commentary.get("highlights") or [])
            if str(line or "").strip()
        ]

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
        commentary: dict[str, Any],
    ) -> None:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        rendered = ChatOperationalDataCommentaryService.render_markdown_sections(commentary)

        if not rendered:
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
        commentary: dict[str, Any],
    ) -> None:
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
