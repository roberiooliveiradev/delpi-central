"""Resposta direta ao inventário de fontes do projeto — sem RAG."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.domain.services.chat_project_sources_intent_service import (
    ChatProjectSourcesIntentService,
)


class ChatProjectSourcesDirectAnswerService:
    @classmethod
    def build_direct_answer(
        cls,
        *,
        message: str,
        user_id: str,
        session,
        workspace_context: dict,
    ) -> str | None:
        if not ChatProjectSourcesIntentService.is_inventory_question(message):
            return None

        project = workspace_context.get("project") if isinstance(workspace_context, dict) else None
        project_id = (
            str((project or {}).get("id") or "").strip()
            or str(getattr(session, "project_id", "") or "").strip()
        )
        project_name = str((project or {}).get("name") or "").strip()

        if not project_id:
            return ChatTurnPreparationContentService.get(
                "directAnswers",
                "projectSources",
                "noProject",
            )

        try:
            from app.composition.chat_composer import make_list_project_sources_use_case

            sources = make_list_project_sources_use_case().execute(
                user_id=str(user_id),
                project_id=project_id,
            )
        except ValueError as exc:
            return ChatTurnPreparationContentService.format(
                "directAnswers",
                "projectSources",
                "loadError",
                error=str(exc),
            )

        if not sources:
            return ChatTurnPreparationContentService.format(
                "directAnswers",
                "projectSources",
                "empty",
                projectName=project_name or "este projeto",
            )

        lines = [
            ChatTurnPreparationContentService.format(
                "directAnswers",
                "projectSources",
                "header",
                projectName=project_name or "Projeto",
            )
        ]

        for source in sources:
            lines.append(cls._format_source_line(source))

        lines.append(
            ChatTurnPreparationContentService.get(
                "directAnswers",
                "projectSources",
                "footer",
            )
        )

        return "\n".join(line for line in lines if line)

    @classmethod
    def _format_source_line(cls, source: Any) -> str:
        metadata = source.metadata if isinstance(source.metadata, dict) else {}
        title = (
            str(source.original_filename or source.title or "Arquivo").strip()
        )
        chunk_count = int(source.chunk_count or 0)
        indexed = bool(source.indexed or chunk_count > 0)
        size_label = cls._format_size(metadata.get("sizeBytes"))

        if str(source.source_type or "").strip() == "project_source" and not metadata.get(
            "originalFilename"
        ):
            template_key = "lineText"
        else:
            template_key = "lineFile"

        status_key = "statusIndexed" if indexed else "statusPending"

        return ChatTurnPreparationContentService.format(
            "directAnswers",
            "projectSources",
            template_key,
            title=title,
            size=size_label or "—",
            chunks=str(chunk_count),
            status=ChatTurnPreparationContentService.get(
                "directAnswers",
                "projectSources",
                status_key,
            ),
        )

    @staticmethod
    def _format_size(size_bytes: object) -> str:
        if not isinstance(size_bytes, (int, float)) or size_bytes <= 0:
            return ""

        value = int(size_bytes)

        if value < 1024:
            return f"{value} B"

        if value < 1024 * 1024:
            return f"{value / 1024:.1f} KB"

        return f"{value / (1024 * 1024):.1f} MB"
