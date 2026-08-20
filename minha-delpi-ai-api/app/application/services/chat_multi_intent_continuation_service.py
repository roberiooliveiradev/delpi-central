"""Continuidade de multi-intent quando o modo limita actions no turno.

Modo Rápida (maxMultiActionsPerTurn=1): executa a 1ª action e oferece chips
«também consultar X» para os escopos adiados — sem chute do LLM.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_product_operational_content_service import (
    ChatProductOperationalContentService,
)

_CONTINUATION_KEY = "_multiActionContinuation"


class ChatMultiIntentContinuationService:
    @classmethod
    def apply_limit(
        cls,
        planned: list[dict],
        *,
        max_calls: int,
    ) -> tuple[list[dict], dict[str, Any] | None]:
        items = [dict(item) for item in planned if isinstance(item, dict)]
        limit = max(1, int(max_calls))

        if len(items) <= limit:
            return items, None

        executed = items[:limit]
        deferred = items[limit:]
        meta = {
            "deferredCount": len(deferred),
            "executedCount": len(executed),
            "deferred": [cls._summarize_deferred(item) for item in deferred],
        }
        first = dict(executed[0])
        first[_CONTINUATION_KEY] = meta
        executed[0] = first

        return executed, meta

    @classmethod
    def strip_from_planned(
        cls,
        planned: list[dict],
    ) -> tuple[list[dict], dict[str, Any] | None]:
        cleaned: list[dict] = []
        continuation: dict[str, Any] | None = None

        for item in planned:
            if not isinstance(item, dict):
                continue

            copy = dict(item)
            marker = copy.pop(_CONTINUATION_KEY, None)

            if isinstance(marker, dict) and not continuation:
                continuation = marker

            cleaned.append(copy)

        return cleaned, continuation

    @classmethod
    def build_follow_up_suggestions(
        cls,
        continuation: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(continuation, dict):
            return []

        deferred = continuation.get("deferred")

        if not isinstance(deferred, list):
            return []

        suggestions: list[dict[str, Any]] = []

        for index, item in enumerate(deferred):
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if not label or not query:
                continue

            suggestions.append(
                {
                    "label": label,
                    "query": query,
                    "group": "continuar",
                    "priority": 20 + index,
                }
            )

        return suggestions

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        tool_context: dict | None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        ctx = tool_context if isinstance(tool_context, dict) else {}
        continuation = ctx.get("multiActionContinuation")

        if not isinstance(continuation, dict):
            selected = ctx.get("selectedExternalAction")

            if isinstance(selected, dict):
                candidate = selected.get("multiActionContinuation")
                continuation = candidate if isinstance(candidate, dict) else None

        suggestions = cls.build_follow_up_suggestions(continuation)

        if not suggestions:
            return

        existing = metadata.get("multiIntentContinuationSuggestions")

        if isinstance(existing, list):
            metadata["multiIntentContinuationSuggestions"] = [
                *existing,
                *suggestions,
            ]
        else:
            metadata["multiIntentContinuationSuggestions"] = suggestions

    @classmethod
    def _summarize_deferred(cls, item: dict) -> dict[str, str]:
        arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        parameters = (
            arguments.get("parameters")
            if isinstance(arguments.get("parameters"), dict)
            else {}
        )
        code = str(
            parameters.get("code")
            or parameters.get("productCode")
            or parameters.get("product_code")
            or ""
        ).strip()
        path = str(arguments.get("path") or item.get("path") or "").strip()
        scope_labels = ChatProductOperationalContentService.scope_labels_from_api_path(
            path
        )
        scope = (
            scope_labels[0]
            if scope_labels
            else ChatProductOperationalContentService.scope_label_for_scope_key(
                "profile",
                default="dados",
            )
        )
        label = ChatProductOperationalContentService.format(
            "multiScope",
            "continueChipLabel",
            scope=scope,
            code=code,
        ) or f"Também consultar {scope}"
        query = ChatProductOperationalContentService.format(
            "multiScope",
            "continueQueryTemplate",
            scope=scope,
            code=code,
        ) or (f"{scope} do produto {code}" if code else scope)

        return {
            "label": label,
            "query": query,
            "scope": scope,
            "productCode": code,
            "path": path,
        }
