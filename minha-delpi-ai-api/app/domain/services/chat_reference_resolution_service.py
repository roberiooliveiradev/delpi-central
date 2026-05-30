"""Resolve referências vagas (follow-up) para entidades da memória de turno."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatReferenceResolutionService:
    @classmethod
    def resolve(
        cls,
        message: str,
        last_entities: dict[str, str] | None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        last_entities = last_entities or {}
        used_keys: list[str] = []
        resolved: list[dict[str, Any]] = []

        if not ChatFollowUpIntentService.is_operational_follow_up(message):
            return resolved, used_keys

        product_code = str(last_entities.get("productCode") or "").strip()
        branch = str(last_entities.get("branch") or "").strip()

        if product_code and not ChatProductQueryIntentService.extract_product_code(message):
            resolved.append(
                {
                    "text": "follow-up operacional",
                    "resolvedTo": "productCode",
                    "value": product_code,
                    "confidence": 0.9,
                }
            )
            used_keys.append("productCode")

        if branch and "filial" not in (message or "").lower():
            resolved.append(
                {
                    "text": "filial em contexto",
                    "resolvedTo": "branch",
                    "value": branch,
                    "confidence": 0.75,
                }
            )
            used_keys.append("branch")

        return resolved, used_keys
