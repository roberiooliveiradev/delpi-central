"""Intenção de visualização — forma dos dados + perfil + mensagem (Playbook 09)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

VIEW_INTENT_AUDITABLE_LIST = "auditable_list"
VIEW_INTENT_RANKING = "ranking"
VIEW_INTENT_TEMPORAL_SERIES = "temporal_series"
VIEW_INTENT_HIERARCHY = "hierarchy"
VIEW_INTENT_SINGLE_METRIC = "single_metric"
VIEW_INTENT_TABLE_ONLY = "table_only"
VIEW_INTENT_UNKNOWN = "unknown"


class ChatPresentationViewIntentService:
    @classmethod
    def prefers_table_for_automatic(
        cls,
        *,
        path: str | None,
        entity: str | None,
        data_shape: dict[str, Any] | None,
        user_message: str | None,
        has_table: bool = True,
    ) -> bool:
        if not has_table:
            return False

        from app.domain.services.chat_presentation_operational_decision_service import (
            ChatPresentationOperationalDecisionService,
        )

        if ChatPresentationOperationalDecisionService.should_prefer_table_over_chart(
            path=path,
            entity=entity,
            has_table=True,
        ):
            return True

        shape = data_shape if isinstance(data_shape, dict) else {}
        view_intent = str(shape.get("viewIntent") or VIEW_INTENT_UNKNOWN).strip().lower()

        if view_intent in {VIEW_INTENT_AUDITABLE_LIST, VIEW_INTENT_TABLE_ONLY}:
            return True

        if view_intent == VIEW_INTENT_RANKING:
            return False

        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())

        if message and cls._message_implies_listing(message):
            return True

        return False

    @classmethod
    def automatic_score_deltas(
        cls,
        *,
        data_shape: dict[str, Any] | None,
        user_message: str | None,
    ) -> dict[str, int]:
        shape = data_shape if isinstance(data_shape, dict) else {}
        view_intent = str(shape.get("viewIntent") or "").strip().lower()
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())

        table_delta = 0
        chart_delta = 0

        if view_intent in {VIEW_INTENT_AUDITABLE_LIST, VIEW_INTENT_TABLE_ONLY}:
            table_delta += 40
            chart_delta -= 30

        if view_intent == VIEW_INTENT_RANKING:
            chart_delta += 15

        if message and cls._message_implies_listing(message):
            table_delta += 35
            chart_delta -= 25

        if message and cls._message_implies_ranking(message):
            chart_delta += 25

        return {"table": table_delta, "chart": chart_delta}

    @classmethod
    def profile_contract_for_entity(cls, entity: str | None) -> dict[str, Any] | None:
        token = str(entity or "").strip()

        if not token:
            return None

        contracts = ChatPresentationProfileService.entity_set_profile_contracts()

        for contract in contracts.values():
            entity_set = contract.get("entitySet") or frozenset()

            if token in entity_set:
                return contract

        return None

    @classmethod
    def _message_implies_listing(cls, message: str) -> bool:
        if cls._message_implies_ranking(message):
            return False

        return any(
            marker in message
            for marker in ChatPresentationVocabularyService.automatic_score_markers("listingMessage")
        )

    @classmethod
    def _message_implies_ranking(cls, message: str) -> bool:
        return any(
            marker in message
            for marker in ChatPresentationVocabularyService.automatic_score_markers("rankingMessage")
        )
