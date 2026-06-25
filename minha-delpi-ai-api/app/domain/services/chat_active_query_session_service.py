"""Sessão de consulta ativa — parâmetros faltantes, resposta curta e continuação até mudança de assunto."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_session_vocabulary_service import (
    ChatSessionVocabularyService,
)
from app.domain.services.chat_web_search_follow_up_service import (
    ChatWebSearchFollowUpService,
)


class ChatActiveQuerySessionService:
    @classmethod
    def _topic_change_markers(cls) -> tuple[str, ...]:
        return ChatSessionVocabularyService.terms("topicChangeMarkers")

    _SUB_INTENT_TO_PRODUCT_INTENT: dict[str, str] = {
        "stock": ChatProductQueryIntent.STOCK,
        "structure": ChatProductQueryIntent.STRUCTURE,
        "parents": ChatProductQueryIntent.PARENTS,
        "description": ChatProductQueryIntent.DESCRIPTION,
        "analyser": ChatProductQueryIntent.ANALYSER,
        "summary": ChatProductQueryIntent.SUMMARY,
        "sales": ChatProductQueryIntent.SALES,
        "factory_status": ChatProductQueryIntent.FULL,
        "production_status": ChatProductQueryIntent.FULL,
        "shipping_status": ChatProductQueryIntent.FULL,
        "raw_material_price_intelligence": ChatProductQueryIntent.FULL,
        "cost_impact_simulation": ChatProductQueryIntent.FULL,
        "last_purchase": ChatProductQueryIntent.FULL,
        "purchase_price_history": ChatProductQueryIntent.FULL,
        "purchase_budget_history": ChatProductQueryIntent.FULL,
        "sale_pricing": ChatProductQueryIntent.FULL,
        "structure_exclusivity": ChatProductQueryIntent.FULL,
        "cost_impact_simulation": ChatProductQueryIntent.FULL,
        "last_purchase": ChatProductQueryIntent.FULL,
        "purchase_price_history": ChatProductQueryIntent.FULL,
        "purchase_budget_history": ChatProductQueryIntent.FULL,
    }

    @classmethod
    def compose_selection_message(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> str:
        from app.application.services.chat_active_pending_service import (
            ChatActivePendingService,
        )

        text = str(message or "").strip()

        pending = ChatActivePendingService.find_from_messages(previous_messages)

        if pending:
            resolved = ChatActivePendingService.try_resolve(text, pending)

            if resolved and resolved.get("resumeMessage"):
                return str(resolved["resumeMessage"])

        session = cls.find_session_from_messages(previous_messages)

        if session and cls.should_continue_session(text, session):
            original = str(session.get("originalMessage") or "").strip()

            if original:
                return f"{original} {text}".strip()

        return text

    @classmethod
    def build_pending_context(
        cls,
        message: str | None,
        *,
        sub_intent: str,
        expected_param: str,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        context: dict[str, str] = {
            "subIntent": sub_intent,
            "expectedParam": expected_param,
            "originalMessage": str(message or "").strip(),
        }

        if extra:
            context.update({key: value for key, value in extra.items() if value})

        return context

    @classmethod
    def find_session_from_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            role = cls._message_role(item)

            if role != "assistant":
                continue

            meta = cls._message_metadata(item)

            if not isinstance(meta, dict):
                continue

            if meta.get("activePending"):
                continue

            session = meta.get("activeQuery")

            if isinstance(session, dict) and session.get("queryKind"):
                return dict(session)

        return None

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        tool_context: dict | None,
        pipeline_stages: list[str] | None,
        previous_messages: list[Any] | None = None,
    ) -> None:
        if "operational_parameter" in list(pipeline_stages or []):
            return

        session = cls.build_session_from_turn(
            message=message,
            tool_context=tool_context,
            previous_messages=previous_messages,
        )

        if not session:
            session = cls._build_web_search_session(
                message=message,
                tool_context=tool_context,
            )

        if session:
            metadata["activeQuery"] = session

    @classmethod
    def _build_web_search_session(
        cls,
        *,
        message: str,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        tool_calls = (tool_context or {}).get("toolCalls") or []

        if not ChatWebSearchFollowUpService.is_primary_web_search_turn(tool_calls):
            return None

        original = str(message or "").strip()

        if not original:
            return None

        return {
            "queryKind": "web_search",
            "subIntent": "web_search",
            "originalMessage": original,
            "expectedParam": "query",
        }

    @classmethod
    def build_session_from_turn(
        cls,
        *,
        message: str,
        tool_context: dict | None,
        previous_messages: list[Any] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        tool_calls = (tool_context or {}).get("toolCalls") or []
        primary_path = cls._primary_successful_action_path(tool_calls)

        if not primary_path:
            return None

        segment = ChatAnalysisIntentService.extract_product_path_segment(primary_path)

        if segment:
            sub_intent = (
                ChatRouteContextService.intent_for_product_segment(segment)
                or ChatProductQueryIntent.FULL
            )
            query_kind = "product_operational"
        else:
            sub_intent = cls._metric_sub_intent_from_path(primary_path)
            query_kind = "metric_operational"

        original = cls._normalize_original_message(
            message,
            expected_param=cls._expected_param_for_sub_intent(sub_intent, segment),
        )

        pending = cls._pending_context_from_messages(previous_messages)

        if pending and str(pending.get("originalMessage") or "").strip():
            original = str(pending["originalMessage"]).strip()

        if not original:
            return None

        session: dict[str, Any] = {
            "queryKind": query_kind,
            "subIntent": sub_intent,
            "originalMessage": original,
            "expectedParam": cls._expected_param_for_sub_intent(sub_intent, segment),
        }

        if segment:
            session["routeSegment"] = segment

        return session

    @classmethod
    def should_continue_session(cls, message: str, session: dict[str, Any]) -> bool:
        text = str(message or "").strip()

        if not text:
            return False

        if cls.looks_like_topic_change(text, session):
            return False

        return cls.looks_like_parameter_only_reply(text, session)

    @classmethod
    def looks_like_topic_change(cls, message: str, session: dict[str, Any] | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatProductQueryIntentService.looks_like_scope_reset_operational_query(message):
            return True

        if any(re.search(pattern, normalized) for pattern in cls._topic_change_markers()):
            return True

        detected = ChatProductQueryIntentService.detect(message)

        if detected == ChatProductQueryIntent.FULL:
            return False

        session_sub = str((session or {}).get("subIntent") or "").strip()
        mapped = cls._SUB_INTENT_TO_PRODUCT_INTENT.get(session_sub, session_sub)

        if mapped and detected != mapped:
            return True

        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        explicit_segment = ChatRouteContextService.segment_from_message(message)
        session_segment = str((session or {}).get("routeSegment") or "").strip()

        if (
            explicit_segment
            and session_segment
            and explicit_segment != session_segment
        ):
            return True

        return False

    @classmethod
    def looks_like_parameter_only_reply(
        cls,
        message: str,
        session: dict[str, Any] | None,
    ) -> bool:
        expected = str((session or {}).get("expectedParam") or "").strip().lower()
        text = str(message or "").strip()

        if not text:
            return False

        if expected in {"productcode", "code"}:
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )

            codes = ChatAnalysisIntentService.extract_all_product_codes(text)

            if not codes:
                return bool(re.fullmatch(r"\d{5,}", text.replace(".", "")))

            if ChatProductQueryIntentService.detect(text) != ChatProductQueryIntent.FULL:
                return False

            return not cls.looks_like_topic_change(text, session)

        if expected in {"period", "date", "reference_date"}:
            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            return ChatOperationalDateParameterService.has_temporal_reference(text)

        if expected == "branch":
            return bool(re.search(r"\b(\d{1,3})\b", text))

        if expected in {"salenumber", "sale_number", "ov"}:
            return bool(re.search(r"\b\d{4,}\b", text.replace(".", "")))

        if expected == "query":
            if cls.looks_like_topic_change(text, session):
                return False

            normalized = ChatMessageNormalizationService.normalize_for_matching(text)

            if any(re.search(pattern, normalized) for pattern in cls._topic_change_markers()):
                return False

            return len(normalized.split()) <= 12

        return False

    @classmethod
    def _normalize_original_message(
        cls,
        message: str,
        *,
        expected_param: str,
    ) -> str:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        original = str(message or "").strip()
        lowered = expected_param.strip().lower()

        if lowered in {"productcode", "code"}:
            for code in ChatAnalysisIntentService.extract_all_product_codes(original):
                original = re.sub(rf"\b{re.escape(code)}\b", " ", original)

            original = re.sub(r"\bproduto\s*$", "", original, flags=re.IGNORECASE)
            original = re.sub(r"\s{2,}", " ", original).strip(" ,;.")

        return original

    @classmethod
    def _expected_param_for_sub_intent(
        cls,
        sub_intent: str,
        route_segment: str | None,
    ) -> str:
        if sub_intent in {
            "factory_status",
            "production_status",
            "shipping_status",
            "period_metric",
            "sales_list",
            "supplies_metric",
            "metric",
        }:
            return "period"

        if route_segment in {
            "factory-status",
            "production-status",
            "shipping-status",
        }:
            return "period"

        return "productCode"

    @classmethod
    def _metric_sub_intent_from_path(cls, path: str) -> str:
        lowered = str(path or "").lower()

        if "/sales" in lowered and "/products/" not in lowered:
            return "sales_list"

        if "/supplies/" in lowered:
            return "supplies_metric"

        return "metric"

    @classmethod
    def _primary_successful_action_path(cls, tool_calls: list) -> str | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata") or {}

            if not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").strip()

            if path:
                return path

        return None

    @classmethod
    def _pending_context_from_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, str] | None:
        from app.application.services.chat_active_pending_service import (
            ChatActivePendingService,
        )

        pending = ChatActivePendingService.find_from_messages(previous_messages)

        if not pending:
            return None

        context = pending.get("context")

        return dict(context) if isinstance(context, dict) else None

    @classmethod
    def _message_role(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            meta = message.get("metadata")

            return dict(meta) if isinstance(meta, dict) else {}

        meta = getattr(message, "metadata", None)

        return dict(meta) if isinstance(meta, dict) else {}
