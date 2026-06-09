"""Parâmetros temporais obrigatórios em consultas operacionais (playbooks e rotas com data)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_DATE_START_KEYS = frozenset(
    {
        "start_date",
        "startdate",
        "data_inicio",
        "data_inicial",
        "date_start",
        "datestart",
    }
)

_DATE_END_KEYS = frozenset(
    {
        "end_date",
        "enddate",
        "data_fim",
        "data_final",
        "date_end",
        "dateend",
    }
)

_DATE_REFERENCE_KEYS = frozenset(
    {
        "reference_date",
        "referencedate",
    }
)

_ALL_DATE_QUERY_KEYS = _DATE_START_KEYS | _DATE_END_KEYS | _DATE_REFERENCE_KEYS

_PLAYBOOK_PATH_MARKERS = (
    "/factory-status",
    "/production-status",
    "/shipping-status",
)


@lru_cache(maxsize=1)
def _parameter_content() -> dict:
    return ChatAssistantContentService.load_bundle("operational_parameters")


class ChatOperationalDateParameterService:
    @classmethod
    def has_temporal_reference(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )
        from app.domain.services.chat_temporal_intent_service import (
            ChatTemporalIntentService,
        )

        if ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        ):
            return True

        return ChatTemporalIntentService.has_temporal_reference(message)

    @classmethod
    def resolve_date_range(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ):
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        return ChatDateRangeIntentService.resolve(
            message,
            previous_messages=previous_messages,
        )

    @classmethod
    def action_has_date_query_params(cls, action: dict) -> bool:
        for parameter in action.get("parametersSchema") or []:
            name = str(parameter.get("name") or "").strip().lower()

            if name in _ALL_DATE_QUERY_KEYS:
                return True

        return False

    @classmethod
    def parameters_have_date(cls, action: dict, parameters: dict) -> bool:
        if not isinstance(parameters, dict):
            return False

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = str(name).strip().lower()

            if lowered not in _ALL_DATE_QUERY_KEYS:
                continue

            value = parameters.get(name)

            if value not in (None, ""):
                return True

        return False

    @classmethod
    def merge_into_parameters(
        cls,
        action: dict,
        message: str | None,
        parameters: dict,
        *,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        from app.domain.services.operational_api_parameter_builder_service import (
            OperationalApiParameterBuilderService,
        )

        builder = OperationalApiParameterBuilderService()
        merged = builder.merge_date_range(
            action,
            message or "",
            parameters,
            previous_messages=previous_messages,
        )

        date_range = cls.resolve_date_range(message, previous_messages=previous_messages)

        if not date_range:
            return merged

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = str(name).strip().lower()

            if lowered in _DATE_REFERENCE_KEYS and name not in merged:
                merged[name] = date_range.start_date

        return merged

    @classmethod
    def message_requires_explicit_date(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        memory_snapshot: dict | None = None,
        conversation_context: str | None = None,
    ) -> bool:
        return cls._missing_date_sub_intent(
            message,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            conversation_context=conversation_context,
        ) is not None

    @classmethod
    def resolve_missing_date_answer(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        memory_snapshot: dict | None = None,
        conversation_context: str | None = None,
    ) -> str | None:
        sub_intent = cls._missing_date_sub_intent(
            message,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            conversation_context=conversation_context,
        )

        if not sub_intent:
            return None

        if cls.has_temporal_reference(message, previous_messages=previous_messages):
            return None

        templates = (_parameter_content().get("missingDateByContext") or {})
        template = templates.get(sub_intent) or templates.get("default")

        if template:
            return str(template).strip()

        fallback = (_parameter_content().get("missingPeriod") or "").strip()

        return fallback or None

    @classmethod
    def compose_selection_message(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> str:
        from app.domain.services.chat_active_query_session_service import (
            ChatActiveQuerySessionService,
        )

        return ChatActiveQuerySessionService.compose_selection_message(
            message,
            previous_messages=previous_messages,
        )

    @classmethod
    def build_pending_context(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        memory_snapshot: dict | None = None,
        conversation_context: str | None = None,
    ) -> dict[str, str]:
        sub_intent = cls._missing_date_sub_intent(
            message,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            conversation_context=conversation_context,
        ) or "default"

        code = ChatProductQueryIntentService.resolve_product_code(
            str(message or ""),
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        context: dict[str, str] = {
            "subIntent": sub_intent,
            "originalMessage": str(message or "").strip(),
        }

        if code:
            context["productCode"] = code

        return context

    @classmethod
    def is_playbook_date_route(cls, path: str | None) -> bool:
        lowered = str(path or "").strip().lower()

        return any(marker in lowered for marker in _PLAYBOOK_PATH_MARKERS)

    @classmethod
    def _missing_date_sub_intent(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        memory_snapshot: dict | None = None,
        conversation_context: str | None = None,
    ) -> str | None:
        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if cls.has_temporal_reference(message, previous_messages=previous_messages):
            return None

        product_code = ChatProductQueryIntentService.resolve_product_code(
            normalized,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if ChatProductQueryIntentService._looks_like_factory_status_question(normalized):
            if product_code or ChatProductQueryIntentService._has_product_scope_reference(
                normalized
            ):
                return "factory_status"

        if ChatProductQueryIntentService._looks_like_production_status_question(normalized):
            if product_code or ChatProductQueryIntentService.extract_product_code(normalized):
                return "production_status"

        if ChatProductQueryIntentService._looks_like_shipping_status_question(normalized):
            if product_code or ChatProductQueryIntentService._has_product_scope_reference(
                normalized
            ):
                return "shipping_status"

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return None

        if ChatProductQueryIntentService._looks_like_structure_question(normalized):
            return None

        if ChatProductQueryIntentService._looks_like_parents_question(normalized):
            return None

        if ChatProductQueryIntentService._looks_like_product_summary_question(normalized):
            return None

        if ChatProductQueryIntentService._looks_like_full_analyser_question(normalized):
            return None

        if ChatDateRangeIntentService.looks_like_period_metric_question(normalized):
            if product_code or ChatProductQueryIntentService._has_product_scope_reference(
                normalized
            ):
                return None

            return "period_metric"

        return None
