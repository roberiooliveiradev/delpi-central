"""Reapresenta o último resultado operacional (tabela/gráfico/texto) sem nova rota errada."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
)
from app.domain.services.chat_presentation_format_vocabulary_service import (
    ChatPresentationFormatVocabularyService,
)


class ChatPresentationFormatRefinementService:
    @classmethod
    def looks_like_format_refinement(cls, message: str | None) -> bool:
        lowered = str(message or "").strip().lower()

        if not lowered:
            return False

        has_format = bool(cls.detect_requested_format(lowered))
        has_reference = any(
            token in lowered for token in ChatPresentationFormatVocabularyService.reference_hints()
        )

        if has_format and has_reference:
            return True

        if has_format and any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.last_result_terms()
        ):
            return True

        if has_format and cls._has_imperative_format_intent(lowered):
            return True

        return False

    @classmethod
    def _has_imperative_format_intent(cls, lowered: str) -> bool:
        if not any(
            verb in lowered for verb in ChatPresentationFormatVocabularyService.imperative_verbs()
        ):
            return False

        return any(
            hint in lowered for hint in ChatPresentationFormatVocabularyService.table_hints()
        ) or any(
            hint in lowered for hint in ChatPresentationFormatVocabularyService.chart_hints()
        ) or any(
            hint in lowered for hint in ChatPresentationFormatVocabularyService.text_hints()
        ) or any(
            hint in lowered for hint in ChatPresentationFormatVocabularyService.tree_hints()
        )

    @classmethod
    def detect_requested_format(cls, message: str) -> str | None:
        lowered = str(message or "").lower()

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.text_hints()):
            return "text"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.tree_hints()):
            return "tree"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.table_hints()):
            return "table"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.chart_hints()):
            return "chart"

        return None

    @classmethod
    def collect_last_successful_operation(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for item in reversed((previous_messages or [])[-16:]):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()

                if "/system/tables" in path:
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                action_id = str(
                    tool_meta.get("actionId") or arguments.get("actionId") or ""
                ).strip()

                if not action_id and not path:
                    continue

                return {
                    "actionId": action_id,
                    "path": str(tool_meta.get("path") or ""),
                    "parameters": dict(parameters),
                    "metadata": dict(tool_meta),
                    "arguments": dict(arguments) if isinstance(arguments, dict) else {},
                }

        return None

    @classmethod
    def resolve_payload(
        cls,
        previous_messages: list[Any] | None,
        *,
        operation: dict[str, Any],
    ) -> object | None:
        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)

        if isinstance(cached, dict) and cached.get("items"):
            return {"data": cached}

        meta = operation.get("metadata") or {}

        for candidate in (
            meta.get("tablePresentation"),
            meta.get("presentation"),
            meta.get("chartPresentation"),
        ):
            if not isinstance(candidate, dict):
                continue

            if candidate.get("type") == "table":
                rows = candidate.get("rows")

                if isinstance(rows, list) and rows:
                    return {
                        "data": {
                            "items": rows,
                            "total": len(rows),
                            "page": 1,
                            "page_size": len(rows),
                            "total_pages": 1,
                        }
                    }

        return None

    @staticmethod
    def _message_metadata(item: Any) -> dict[str, Any]:
        if hasattr(item, "metadata"):
            metadata = getattr(item, "metadata", None)

            return metadata if isinstance(metadata, dict) else {}

        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        return {}
