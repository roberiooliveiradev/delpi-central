"""P2 — pipeline data-only: não gerar prosa template quando LLM narrará o turno."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_prose_delivery_service import (
    MODE_LLM,
    ChatPresentationProseDeliveryService,
)


class ChatPresentationDataOnlyProseService:
    FLAG = "dataOnlyPresentation"

    @classmethod
    def should_apply(cls, user_message: str | None, *, path: str | None = None) -> bool:
        return ChatPresentationProseDeliveryService.should_skip_template_prose_in_pipeline(
            user_message,
            path=path,
        )

    @classmethod
    def is_data_only_metadata(cls, metadata: dict[str, Any] | None) -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get(cls.FLAG):
            return True

        return ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(metadata)

    @classmethod
    def mark_metadata(cls, metadata: dict[str, Any]) -> None:
        metadata[cls.FLAG] = True
        metadata["proseDeliveryMode"] = MODE_LLM

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["proseSource"] = MODE_LLM

    @classmethod
    def archive_and_strip_humanized(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        humanized = metadata.get("humanizedSummary")
        archived_humanized: dict[str, Any] | None = None

        if isinstance(humanized, dict):
            archived_humanized = {
                key: value
                for key, value in humanized.items()
                if value not in (None, "", [])
            }

        text_presentation = metadata.get("textPresentation")
        archived_markdown = ""

        if isinstance(text_presentation, dict):
            archived_markdown = str(text_presentation.get("markdown") or "").strip()

        if archived_markdown or archived_humanized:
            archive = metadata.get("templateProseArchive")

            if not isinstance(archive, dict):
                archive = {}

            if archived_markdown:
                archive["textPresentationMarkdown"] = archived_markdown

            if archived_humanized:
                archive["humanizedSummary"] = archived_humanized

            metadata["templateProseArchive"] = archive

        if isinstance(text_presentation, dict):
            text_presentation["markdown"] = ""

        if isinstance(humanized, dict):
            humanized["linhas"] = []
            humanized["linhas_detalhe"] = []

        metadata.pop("storyPresentation", None)

    @classmethod
    def prepare_humanized_for_metadata(
        cls,
        metadata: dict[str, Any],
        humanized: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not cls.is_data_only_metadata(metadata):
            return humanized

        if not isinstance(humanized, dict):
            return humanized

        titulo = str(humanized.get("titulo") or "").strip()
        linhas = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]
        detail_lines = [
            str(line).strip()
            for line in (humanized.get("linhas_detalhe") or [])
            if str(line or "").strip()
        ]

        if linhas or detail_lines:
            archive = metadata.get("templateProseArchive")

            if not isinstance(archive, dict):
                archive = {}

            archive["humanizedSummary"] = {
                **({"titulo": titulo} if titulo else {}),
                **({"linhas": linhas} if linhas else {}),
                **({"linhas_detalhe": detail_lines} if detail_lines else {}),
            }
            metadata["templateProseArchive"] = archive

        return {"titulo": titulo} if titulo else None

    @classmethod
    def finalize_metadata(cls, metadata: dict[str, Any]) -> None:
        if not cls.is_data_only_metadata(metadata):
            return

        cls.archive_and_strip_humanized(metadata)
        cls.mark_metadata(metadata)
        metadata["llmProseDecoupled"] = True

        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationRenderPipelineService.finalize(metadata)
