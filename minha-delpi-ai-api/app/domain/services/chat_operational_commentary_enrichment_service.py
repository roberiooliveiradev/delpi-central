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
from app.domain.services.chat_presentation_scalar_field_commentary_service import (
    ChatPresentationScalarFieldCommentaryService,
)


class ChatDataInsightEnrichmentService:
    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        data: dict[str, Any] | None = None,
        format_quantity=None,
        user_message: str | None = None,
    ) -> None:
        if not isinstance(metadata, dict) or not isinstance(data, dict):
            return

        if user_message:
            metadata["userMessage"] = user_message

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

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if ChatPresentationProseDeliveryService.should_block_template_prose_metadata(metadata):
            ChatPresentationScalarFieldCommentaryService.apply_text_presentation(metadata, data_answer)
            return

        cls._merge_humanized_summary(metadata, commentary or data_answer)
        ChatPresentationScalarFieldCommentaryService.apply_text_presentation(metadata, data_answer)
        cls._ensure_text_markdown_commentary(metadata, commentary)
        cls._append_narrative_closing(metadata, commentary)
        cls._apply_template_verdict_lead(metadata, data, user_message)

    @classmethod
    def _merge_humanized_summary(
        cls,
        metadata: dict[str, Any],
        commentary_or_answer: dict[str, Any],
    ) -> None:
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        humanized = metadata.get("humanizedSummary")

        if not isinstance(humanized, dict):
            humanized = {}

        existing = [
            str(line).strip()
            for line in ChatPresentationProseDeliveryService.resolve_humanized_lines_for_display(
                metadata,
            )
            if str(line or "").strip()
        ]

        summary_block = commentary_or_answer.get("summary")
        summary = ""

        if isinstance(summary_block, dict):
            summary = str(summary_block.get("answer") or "").strip()
        else:
            summary = str(commentary_or_answer.get("summary") or "").strip()

        if summary and ChatPresentationScalarFieldCommentaryService._is_empty_list_summary(summary):
            summary = ""

        commentary_lines = [summary] if summary else []
        commentary_lines.extend(
            str(line).strip()
            for line in (
                commentary_or_answer.get("summaryLines")
                or commentary_or_answer.get("highlights")
                or []
            )
            if str(line or "").strip()
            and str(line).strip() not in commentary_lines
            and not ChatPresentationScalarFieldCommentaryService._is_empty_list_summary(str(line))
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
    def _apply_template_verdict_lead(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
        user_message: str | None,
    ) -> None:
        """Perfis preserve_template materializam o veredito da síntese no markdown.

        A síntese é omitida do dataAnswer (evita duplicação com o template), então o
        veredito precisa liderar o texto — caso contrário o markdown fica genérico.
        """
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if not ChatPresentationProseDeliveryService.should_skip_question_synthesis_verdict(
            metadata,
        ):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        message = str(user_message or metadata.get("userMessage") or "").strip()

        if not message:
            return

        from app.domain.services.chat_operational_user_question_synthesis_service import (
            ChatOperationalUserQuestionSynthesisService,
        )

        data_answer = metadata.get("dataAnswer")
        profile_key = str(
            (data_answer or {}).get("profileKey") if isinstance(data_answer, dict) else "",
        ).strip()
        entity = cls._resolve_entity_token(metadata, data)

        synthesis = ChatOperationalUserQuestionSynthesisService.try_synthesize(
            message,
            data,
            profile_key=profile_key,
            entity=entity,
        )

        if not synthesis:
            return

        verdict = str(synthesis.get("summary") or "").strip()

        if not verdict:
            return

        interpretation = str(synthesis.get("interpretation") or "").strip()
        body = verdict if not interpretation else f"{verdict}\n\n{interpretation}"
        text_presentation["markdown"] = cls._replace_scope_lead(
            str(text_presentation.get("markdown") or ""),
            body,
        )

    @staticmethod
    def _resolve_entity_token(metadata: dict[str, Any], data: dict[str, Any]) -> str:
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            token = str(api_meta.get("entity") or "").strip()

            if token:
                return token

        return str(data.get("entity") or "").strip()

    @staticmethod
    def _replace_scope_lead(markdown: str, body: str) -> str:
        marker = "<!-- section:scope -->"
        head, sep, _ = markdown.partition(marker)

        if not sep:
            title = head.strip()

            return f"{title}\n\n{marker}\n\n{body}".strip() if title else body

        return f"{head.rstrip()}\n\n{marker}\n\n{body}".strip()

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
