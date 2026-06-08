"""Recuperação automática após erro/vazio — Playbook 06 Fase 4."""

from __future__ import annotations

import copy
from functools import lru_cache
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("error_handling")


class ChatErrorAutoRecoveryService:
    @classmethod
    def build_plan(
        cls,
        *,
        error_type: str,
        tool_calls: list | None,
        previous_messages: list[Any] | None = None,
    ) -> dict[str, Any] | None:
        if not cls._type_supports_auto_recovery(error_type):
            return None

        operation = cls.collect_operation(
            tool_calls,
            previous_messages=previous_messages,
            prefer_failed=True,
        )

        if not operation:
            operation = cls.collect_operation(
                tool_calls,
                previous_messages=previous_messages,
                prefer_failed=False,
            )

        if not operation:
            return None

        default_strategy = cls._default_strategy_for_type(error_type)

        return {
            "strategy": default_strategy,
            "errorType": error_type,
            "actionId": operation.get("actionId"),
            "path": operation.get("path"),
            "parameters": dict(operation.get("parameters") or {}),
        }

    @classmethod
    def looks_like_recovery_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(
            message or "",
        )

        if not normalized:
            return False

        config = _content().get("autoRecovery") or {}
        triggers = config.get("retryTriggers") or []

        for token in triggers:
            if str(token).strip().lower() in normalized:
                return True

        chip_queries = _content().get("chipQueries") or {}

        for label, query in chip_queries.items():
            if label in ("Tentar novamente", "Tentar mais tarde", "Remover filtros", "Ampliar período"):
                if str(query).strip().lower() in normalized:
                    return True

        return False

    @classmethod
    def resolve_strategy(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(
            message or "",
        )
        config = _content().get("autoRecovery") or {}

        for label, strategy in (config.get("strategyByChipLabel") or {}).items():
            query = (_content().get("chipQueries") or {}).get(label) or label

            if str(query).strip().lower() in normalized:
                return str(strategy)

        if any(
            token in normalized
            for token in (config.get("removeFiltersTriggers") or [])
        ):
            return "remove_filters"

        if any(token in normalized for token in (config.get("widenPeriodTriggers") or [])):
            return "widen_period"

        return "retry_last"

    @classmethod
    def collect_operation(
        cls,
        tool_calls: list | None,
        *,
        previous_messages: list[Any] | None = None,
        prefer_failed: bool = False,
    ) -> dict[str, Any] | None:
        candidates: list[dict[str, Any]] = []

        for source in (tool_calls, cls._tool_calls_from_history(previous_messages)):
            if not source:
                continue

            for call in reversed(source):
                if not isinstance(call, dict):
                    continue

                if str(call.get("name") or "") != "execute_external_action":
                    continue

                metadata = call.get("metadata") or {}
                arguments = call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                action_id = str(
                    metadata.get("actionId")
                    or arguments.get("actionId")
                    or ""
                ).strip()
                path = str(metadata.get("path") or "")

                if not action_id and not path:
                    continue

                ok = bool(metadata.get("ok"))
                candidates.append(
                    {
                        "actionId": action_id,
                        "path": path,
                        "parameters": dict(parameters),
                        "ok": ok,
                    }
                )

        if prefer_failed:
            for item in candidates:
                if not item.get("ok"):
                    return item

        return candidates[0] if candidates else None

    @classmethod
    def apply_strategy(
        cls,
        strategy: str,
        operation: dict[str, Any],
        message: str,
    ) -> dict[str, Any]:
        parameters = copy.deepcopy(operation.get("parameters") or {})

        if strategy == "remove_filters":
            for key in (
                "branch",
                "warehouse",
                "filial",
                "armazem",
                "period",
                "period_start",
                "period_end",
                "date_from",
                "date_to",
                "start_date",
                "end_date",
            ):
                parameters.pop(key, None)

        elif strategy == "widen_period":
            for key in ("period_start", "period_end", "date_from", "date_to", "start_date", "end_date"):
                parameters.pop(key, None)

            page_size = parameters.get("page_size")

            if isinstance(page_size, int) and page_size < 100:
                parameters["page_size"] = min(page_size * 2, 100)

        elif strategy == "retry_last":
            pass

        return parameters

    @classmethod
    def _tool_calls_from_history(
        cls,
        previous_messages: list[Any] | None,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []

        for item in reversed((previous_messages or [])[-12:]):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            if isinstance(tool_calls, list):
                collected.extend(call for call in tool_calls if isinstance(call, dict))

        return collected

    @classmethod
    def _message_metadata(cls, item: Any) -> dict[str, Any]:
        if hasattr(item, "metadata"):
            metadata = getattr(item, "metadata", None)

            return metadata if isinstance(metadata, dict) else {}

        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        return {}

    @classmethod
    def _type_supports_auto_recovery(cls, error_type: str) -> bool:
        config = (_content().get("autoRecovery") or {}).get("strategiesByType") or {}

        return error_type in config

    @classmethod
    def _default_strategy_for_type(cls, error_type: str) -> str:
        config = (_content().get("autoRecovery") or {}).get("strategiesByType") or {}
        value = config.get(error_type)

        return str(value or "retry_last")
