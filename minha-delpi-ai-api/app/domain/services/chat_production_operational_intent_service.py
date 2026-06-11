"""Intenções operacionais de produção, compras ranking e perdas — Playbook 15 Fase 1."""

from __future__ import annotations

from enum import Enum

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ProductionOperationalIntentKind(str, Enum):
    CONSUMPTION = "consumption"
    CONSUMPTION_BY_WORK_CENTER = "consumptionByWorkCenter"
    CONSUMPTION_VALIDATED = "consumptionValidated"
    PURCHASES_RANKING = "purchasesRanking"
    LOSSES_TOP = "lossesTop"
    LOSSES_RECORDS = "lossesRecords"
    SCHEDULE_TODAY = "scheduleToday"
    ORDERS_OPEN = "ordersOpen"
    ORDERS_FINISHED = "ordersFinished"
    WORK_CENTER_SUMMARY = "workCenterSummary"


_BUNDLE = "production_operational_intent"


class ChatProductionOperationalIntentService:
    @classmethod
    def _terms(cls, section: str, key: str = "terms") -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, section, key))

    @classmethod
    def _path_token(cls, kind: ProductionOperationalIntentKind) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "pathTokens",
                kind.value,
                default="",
            )
            or ""
        ).lower()

    @classmethod
    def resolve(cls, message: str | None) -> ProductionOperationalIntentKind | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        for kind in (
            ProductionOperationalIntentKind.LOSSES_RECORDS,
            ProductionOperationalIntentKind.CONSUMPTION_BY_WORK_CENTER,
            ProductionOperationalIntentKind.CONSUMPTION_VALIDATED,
            ProductionOperationalIntentKind.WORK_CENTER_SUMMARY,
            ProductionOperationalIntentKind.ORDERS_FINISHED,
            ProductionOperationalIntentKind.ORDERS_OPEN,
            ProductionOperationalIntentKind.SCHEDULE_TODAY,
            ProductionOperationalIntentKind.PURCHASES_RANKING,
            ProductionOperationalIntentKind.CONSUMPTION,
            ProductionOperationalIntentKind.LOSSES_TOP,
        ):
            if cls._matches_kind(normalized, message or "", kind):
                return kind

        return None

    @classmethod
    def _matches_kind(
        cls,
        normalized: str,
        message: str,
        kind: ProductionOperationalIntentKind,
    ) -> bool:
        if any(term in normalized for term in cls._terms(kind.value, "excludeTerms")):
            return False

        if not any(term in normalized for term in cls._terms(kind.value, "terms")):
            return False

        if kind == ProductionOperationalIntentKind.PURCHASES_RANKING:
            if ChatProductQueryIntentService.extract_product_code(message):
                if any(
                    marker in normalized
                    for marker in ("ultima compra", "última compra", "ultimo fornecedor")
                ):
                    return False

        if kind == ProductionOperationalIntentKind.CONSUMPTION:
            if "comprad" in normalized or " compra " in f" {normalized} ":
                return False

        return True

    @classmethod
    def infer_loss_type(cls, normalized: str) -> str | None:
        if any(
            term in normalized
            for term in ChatAssistantContentService.list(_BUNDLE, "lossTypeScrap")
        ):
            return "scrap"
        if any(
            term in normalized
            for term in ChatAssistantContentService.list(_BUNDLE, "lossTypeRefugo")
        ):
            return "refugo"
        return None

    @classmethod
    def path_token_for(cls, kind: ProductionOperationalIntentKind) -> str:
        return cls._path_token(kind)

    @classmethod
    def matches_rest_route(cls, message: str | None) -> bool:
        return cls.resolve(message) is not None
