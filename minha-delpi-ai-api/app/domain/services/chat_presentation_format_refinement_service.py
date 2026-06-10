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
        meta = operation.get("metadata") or {}

        consolidation = meta.get("paginationConsolidation")

        if isinstance(consolidation, dict):
            consolidated = consolidation.get("consolidatedPayload")

            if isinstance(consolidated, dict) and consolidated.get("items"):
                return cls.wrap_payload_for_operation(operation, consolidated)

        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)

        if isinstance(cached, dict) and cached.get("items"):
            return cls.wrap_payload_for_operation(operation, cached)

        for candidate in cls._iter_table_candidates(meta):
            if candidate.get("type") != "table":
                continue

            root = cls._rows_payload_from_table(candidate)

            if root:
                return cls.wrap_payload_for_operation(operation, root)

        return None

    @classmethod
    def wrap_payload_for_operation(cls, operation: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
        path = str(operation.get("path") or "").lower()
        items = root.get("items")

        if not isinstance(items, list):
            return {"data": root}

        payload_root = dict(root)

        if "/stock" in path:
            return {"data": {"stock": payload_root}}

        return {"data": payload_root}

    @classmethod
    def rebuild_metadata_for_refinement(
        cls,
        *,
        external_use_case,
        operation: dict[str, Any],
        payload: object,
        requested_format: str | None,
        user_message: str | None,
    ) -> dict[str, Any] | None:
        action_id = str(operation.get("actionId") or "").strip()

        if not action_id or payload is None or external_use_case is None:
            return None

        parameters = dict(operation.get("parameters") or {})

        if requested_format:
            parameters["sessionResponseFormat"] = requested_format

        if user_message:
            parameters["userMessage"] = user_message

        try:
            rebuilt = external_use_case.build_metadata_for_data(
                action_id=action_id,
                data=payload,
                parameters=parameters,
            )
        except ValueError:
            return None

        prior = operation.get("metadata") or {}

        for key in (
            "ok",
            "statusCode",
            "actionId",
            "path",
            "provider",
            "method",
            "operationId",
            "apiDelpiResponseMeta",
        ):
            if key in prior:
                rebuilt[key] = prior[key]

        consolidation = prior.get("paginationConsolidation")

        if isinstance(consolidation, dict):
            rebuilt["paginationConsolidation"] = dict(consolidation)

        return rebuilt

    @classmethod
    def _iter_table_candidates(cls, meta: dict[str, Any]):
        for key in ("tablePresentation", "presentation", "chartPresentation"):
            candidate = meta.get(key)

            if isinstance(candidate, dict):
                yield candidate

        bulk = meta.get("tablePresentations")

        if isinstance(bulk, list):
            for candidate in reversed(bulk):
                if isinstance(candidate, dict):
                    yield candidate

    @classmethod
    def _rows_payload_from_table(cls, table: dict[str, Any]) -> dict[str, Any] | None:
        rows = table.get("rows")

        if not isinstance(rows, list) or not rows:
            return None

        return {
            "items": rows,
            "total": len(rows),
            "page": 1,
            "page_size": len(rows),
            "total_pages": 1,
        }

    @staticmethod
    def _message_metadata(item: Any) -> dict[str, Any]:
        if hasattr(item, "metadata"):
            metadata = getattr(item, "metadata", None)

            return metadata if isinstance(metadata, dict) else {}

        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        return {}
