"""Roteamento declarativo de follow-ups operacionais — operational_follow_up_routing.json."""

from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@lru_cache(maxsize=1)
def _routing_content() -> dict:
    return ChatAssistantContentService.load_bundle("operational_follow_up_routing")


class ChatOperationalFollowUpRoutingService:
    """Flags e segmentos de rota por follow_up_type — fonte única para matcher, data e capabilities."""

    @classmethod
    def _follow_up_types(cls) -> dict:
        types = _routing_content().get("followUpTypes")

        return types if isinstance(types, dict) else {}

    @classmethod
    def type_config(cls, follow_up_type: str | None) -> dict:
        key = str(follow_up_type or "").strip()

        if not key:
            return {}

        config = cls._follow_up_types().get(key)

        return config if isinstance(config, dict) else {}

    @classmethod
    def playbook_path_markers(cls) -> tuple[str, ...]:
        markers = _routing_content().get("playbookPathMarkers") or []

        return tuple(str(item) for item in markers if str(item).strip())

    @classmethod
    def route_segment(cls, follow_up_type: str | None) -> str | None:
        segment = str(cls.type_config(follow_up_type).get("routeSegment") or "").strip()

        return segment or None

    @classmethod
    def preferred_route_id(cls, follow_up_type: str | None) -> str | None:
        route_id = str(cls.type_config(follow_up_type).get("preferredRouteId") or "").strip()

        return route_id or None

    @classmethod
    def inherits_playbook_date(cls, follow_up_type: str | None) -> bool:
        if not follow_up_type:
            return False

        if bool(cls.type_config(follow_up_type).get("inheritsPlaybookDate")):
            return True

        configured = _routing_content().get("dateInheritance") or {}

        if not isinstance(configured, dict):
            return False

        allowed = configured.get("followUpTypes") or []

        return follow_up_type in {str(item) for item in allowed if str(item).strip()}

    @classmethod
    def grants_product_scope(cls, follow_up_type: str | None) -> bool:
        return bool(cls.type_config(follow_up_type).get("grantsProductScope"))

    @classmethod
    def grants_specific_product_scope(cls, follow_up_type: str | None) -> bool:
        return bool(cls.type_config(follow_up_type).get("grantsSpecificProductScope"))

    @classmethod
    def message_segment_terms(cls) -> tuple[tuple[str, tuple[str, ...]], ...]:
        parsed: list[tuple[str, tuple[str, ...]]] = []

        for follow_up_type, config in cls._follow_up_types().items():
            if not isinstance(config, dict):
                continue

            segment = str(config.get("routeSegment") or "").strip()
            terms = config.get("messageSegmentTerms") or []

            if not segment or not isinstance(terms, list):
                continue

            parsed.append(
                (
                    segment,
                    tuple(str(term) for term in terms if str(term).strip()),
                )
            )

        return tuple(parsed)

    @classmethod
    def segment_from_message(cls, message: str | None) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        for segment, terms in cls.message_segment_terms():
            if any(term in normalized for term in terms):
                return segment

        return None

    @classmethod
    def looks_like_playbook_date_follow_up(
        cls,
        message: str | None,
        *,
        normalized: str | None = None,
    ) -> bool:
        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if not normalized_text:
            return False

        follow_up_type = ChatFollowUpIntentService.follow_up_type(message)

        if follow_up_type and cls.inherits_playbook_date(follow_up_type):
            return True

        date_config = _routing_content().get("dateInheritance") or {}

        if isinstance(date_config, dict) and ChatFollowUpIntentService.is_operational_follow_up(
            message
        ):
            segment = cls.segment_from_message(message)

            if segment and segment in {
                str(item)
                for item in (date_config.get("routeSegments") or [])
                if str(item).strip()
            }:
                return True

        if not ChatProductQueryIntentService.references_previous_product(message or ""):
            return False

        predicates = (
            date_config.get("productPredicatesWhenReferencingPrevious")
            if isinstance(date_config, dict)
            else []
        )

        for predicate in predicates or []:
            if ChatProductQueryIntentService._matches_product_predicate(
                str(predicate),
                normalized_text,
            ):
                return True

        return False

    @classmethod
    def blocks_capability_inquiry(
        cls,
        message: str | None,
        *,
        normalized: str | None = None,
        operational_data_topics: tuple[str, ...] = (),
    ) -> bool:
        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )

        gate = _routing_content().get("capabilitiesGate") or {}

        if not isinstance(gate, dict):
            return False

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if gate.get("blockOnOperationalFollowUp") and ChatFollowUpIntentService.is_operational_follow_up(
            message
        ):
            return True

        if gate.get("blockOnStructureExclusivityQuestion") and (
            ChatProductQueryIntentService.looks_like_structure_exclusivity_question(message)
        ):
            return True

        if gate.get("blockOnReferencesPreviousWithOperationalTopics") and (
            ChatProductQueryIntentService.references_previous_product(message or "")
        ):
            if operational_data_topics and any(
                topic in normalized_text for topic in operational_data_topics
            ):
                return True

        return False
