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

_OPTIONAL_DATE_PATH_MARKERS = (
    "/raw-material-price-intelligence",
    "/last-purchase",
    "/purchase-price-history",
    "/purchase-budget-history",
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

        if ChatTemporalIntentService.has_temporal_reference(message):
            return True

        if cls._can_inherit_playbook_date(message, previous_messages=previous_messages):
            return True

        return False

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
    def action_requires_explicit_date(cls, action: dict) -> bool:
        if not cls.action_has_date_query_params(action):
            return False

        path = str(action.get("path") or "").lower()

        if any(marker in path for marker in _OPTIONAL_DATE_PATH_MARKERS):
            return False

        return cls.is_playbook_date_route(path)

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

        if date_range:
            for parameter in action.get("parametersSchema") or []:
                name = parameter.get("name")

                if not name:
                    continue

                lowered = str(name).strip().lower()

                if lowered in _DATE_REFERENCE_KEYS and name not in merged:
                    merged[name] = date_range.start_date

            return merged

        if cls._can_inherit_playbook_date(message, previous_messages=previous_messages):
            inherited = cls.collect_recent_playbook_date_parameters(previous_messages)

            for parameter in action.get("parametersSchema") or []:
                name = parameter.get("name")

                if not name or name in merged:
                    continue

                lowered = str(name).strip().lower()

                if lowered not in _ALL_DATE_QUERY_KEYS:
                    continue

                for candidate_key, candidate_value in inherited.items():
                    if str(candidate_key).strip().lower() != lowered:
                        continue

                    if candidate_value not in (None, ""):
                        merged[name] = candidate_value

                    break

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
    def collect_recent_playbook_date_parameters(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, str]:
        """Reutiliza parâmetros temporais do último turno playbook bem-sucedido."""
        if not previous_messages:
            return {}

        for item in reversed(previous_messages[-14:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")

                if not cls.is_playbook_date_route(path):
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}
                extracted = cls._extract_date_parameter_values(parameters)

                if extracted:
                    return extracted

        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        for item in reversed(previous_messages[-10:]):
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item)

            if not content.strip():
                continue

            date_range = ChatDateRangeIntentService.resolve(content)

            if not date_range:
                continue

            return cls._parameters_from_date_range(date_range)

        return {}

    @classmethod
    def _can_inherit_playbook_date(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if not previous_messages:
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not cls._looks_like_playbook_date_follow_up(message, normalized=normalized):
            return False

        return bool(cls.collect_recent_playbook_date_parameters(previous_messages))

    @classmethod
    def _looks_like_playbook_date_follow_up(
        cls,
        message: str | None,
        *,
        normalized: str | None = None,
    ) -> bool:
        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if not normalized_text:
            return False

        if ChatFollowUpIntentService.is_operational_follow_up(message):
            follow_type = ChatFollowUpIntentService.follow_up_type(message)

            if follow_type in {"shipping", "structure", "structure_exclusivity"}:
                return True

            segment = ChatRouteContextService.segment_from_message(message or "")

            if segment in {"factory-status", "production-status", "shipping-status"}:
                return True

        if ChatProductQueryIntentService.references_previous_product(message or ""):
            if ChatProductQueryIntentService._looks_like_shipping_status_question(
                normalized_text
            ):
                return True

            if ChatProductQueryIntentService._looks_like_production_status_question(
                normalized_text
            ):
                return True

            if ChatProductQueryIntentService._looks_like_factory_status_question(
                normalized_text
            ):
                return True

        return False

    @staticmethod
    def _extract_date_parameter_values(parameters: dict | None) -> dict[str, str]:
        if not isinstance(parameters, dict):
            return {}

        extracted: dict[str, str] = {}

        for name, value in parameters.items():
            lowered = str(name or "").strip().lower()

            if lowered not in _ALL_DATE_QUERY_KEYS:
                continue

            if value in (None, ""):
                continue

            extracted[str(name)] = str(value)

        return extracted

    @staticmethod
    def _parameters_from_date_range(date_range) -> dict[str, str]:
        return {
            "reference_date": date_range.start_date,
            "date_start": date_range.start_date,
            "date_end": date_range.end_date,
            "start_date": date_range.start_date,
            "end_date": date_range.end_date,
        }

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @staticmethod
    def _message_role(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @staticmethod
    def _message_content(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

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

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
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
