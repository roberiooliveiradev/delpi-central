"""Resposta direta PT-BR para narrate grounded (excerpt + último resultado operacional)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_tool_summary_resolution_service import (
    ChatOperationalToolSummaryResolutionService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)

_CONTENT_BUNDLE = "turn_grounding"


class ChatGroundedNarrateAnswerService:
    @classmethod
    def build_answer(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
    ) -> str | None:
        context = tool_context if isinstance(tool_context, dict) else {}

        if not context.get("groundedNarrate"):
            return None

        excerpt = cls._resolve_excerpt(workspace_context, tool_context)

        if not isinstance(excerpt, dict) or not excerpt:
            return None

        from app.application.services.chat_data_interpretation_answer_service import (
            ChatDataInterpretationAnswerService,
        )

        interpreted = ChatDataInterpretationAnswerService.build_answer(
            message,
            previous_messages,
        )

        if interpreted:
            return interpreted

        summary = cls._resolve_latest_summary(previous_messages)

        if summary:
            title = str(summary.get("titulo") or excerpt.get("title") or "").strip()
            lines = [
                str(line).strip()
                for line in (summary.get("linhas") or [])
                if str(line or "").strip()
            ]

            if lines:
                intro = ChatAssistantContentService.format(
                    _CONTENT_BUNDLE,
                    "narrateAnswer",
                    "summaryIntro",
                    default="Com base no último resultado (**{title}**):",
                    title=title or ChatTurnGroundingContentService.last_result_heading(),
                )
                body = "\n".join(f"- {line}" for line in lines[:12])
                parts = [intro.strip(), body]

                if len(lines) > 12:
                    parts.append(
                        ChatAssistantContentService.format(
                            _CONTENT_BUNDLE,
                            "narrateAnswer",
                            "truncatedTail",
                            default="_… e mais {extra} detalhe(s) na consulta original._",
                            extra=len(lines) - 12,
                        )
                    )

                return "\n\n".join(part for part in parts if part)

        return cls._build_from_excerpt(excerpt)

    @classmethod
    def _resolve_excerpt(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        if isinstance(tool_context, dict):
            turn_grounding = tool_context.get("turnGrounding")

            if isinstance(turn_grounding, dict):
                excerpt = turn_grounding.get("excerpt")

                if isinstance(excerpt, dict) and excerpt:
                    return excerpt

        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        turn_grounding = workspace.get("turnGrounding")

        if isinstance(turn_grounding, dict):
            excerpt = turn_grounding.get("excerpt")

            if isinstance(excerpt, dict) and excerpt:
                return excerpt

        working = workspace.get("workingMemory")

        if isinstance(working, dict):
            excerpt = working.get("lastResultExcerpt")

            if isinstance(excerpt, dict) and excerpt:
                return excerpt

        return None

    @classmethod
    def _resolve_latest_summary(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        if not previous_messages:
            return None

        for item in reversed(previous_messages[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                summary = ChatOperationalToolSummaryResolutionService.resolve_tool_summary(
                    tool_meta,
                )

                if summary:
                    return summary

        return None

    @classmethod
    def _build_from_excerpt(cls, excerpt: dict[str, Any]) -> str | None:
        title = str(excerpt.get("title") or "").strip() or ChatTurnGroundingContentService.last_result_heading()
        row_count = excerpt.get("rowCount")
        top_keys = [
            str(code).strip()
            for code in (excerpt.get("topKeys") or [])
            if str(code).strip()
        ]

        if not top_keys and not (isinstance(row_count, int) and row_count > 0):
            return None

        count = int(row_count) if isinstance(row_count, int) and row_count > 0 else len(top_keys)

        intro = ChatAssistantContentService.format(
            _CONTENT_BUNDLE,
            "narrateAnswer",
            "itemsIntro",
            default="Com base no último resultado (**{title}**), há **{rowCount}** itens em foco.",
            title=title,
            rowCount=count,
        )

        parts = [intro.strip()]

        if top_keys:
            heading = str(
                ChatAssistantContentService.get(
                    _CONTENT_BUNDLE,
                    "narrateAnswer",
                    "itemsListHeading",
                    default="Códigos principais:",
                )
                or "Códigos principais:"
            ).strip()
            lines = [
                ChatAssistantContentService.format(
                    _CONTENT_BUNDLE,
                    "narrateAnswer",
                    "itemsListLine",
                    default="- {code}",
                    code=code,
                )
                for code in top_keys[: ChatTurnGroundingContentService.max_top_keys()]
            ]
            parts.append(f"{heading}\n" + "\n".join(lines))

        outro = str(
            ChatAssistantContentService.get(
                _CONTENT_BUNDLE,
                "narrateAnswer",
                "itemsOutro",
                default="",
            )
            or ""
        ).strip()

        if outro:
            parts.append(outro)

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)
        return metadata if isinstance(metadata, dict) else {}
