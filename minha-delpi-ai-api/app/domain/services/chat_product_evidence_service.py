"""Evidência de produto para compare BOM / estrutura — família declarativa, sem if path."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)


class ChatProductEvidenceService:
    """True quando a mensagem traz código ou o lastAction é família product/structure."""

    _PRODUCT_FAMILIES = frozenset({"product", "structure"})

    @classmethod
    def has_product_evidence(
        cls,
        message: str | None,
        *,
        last_action: dict[str, Any] | None = None,
        conversation_context: str | None = None,
    ) -> bool:
        codes = ChatAnalysisIntentService.extract_all_product_codes(
            message,
            conversation_context,
        )
        if codes:
            return True

        action = last_action if isinstance(last_action, dict) else None
        if not action:
            return False

        family = ChatFollowUpTurnContentService.entity_family_for_markers(
            str(action.get("apiRouteDomain") or ""),
            str(action.get("resultType") or ""),
            str(action.get("name") or ""),
            str(action.get("path") or ""),
            str(action.get("parameterStrategy") or ""),
        )
        if family in cls._PRODUCT_FAMILIES:
            return True

        if family == "metric":
            return False

        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        product_code = str(params.get("productCode") or params.get("code") or "").strip()
        if not product_code:
            return False

        # Código nos params só conta se o envelope ainda sugerir produto/estrutura.
        inferred = ChatFollowUpTurnContentService.entity_family_for_markers(
            str(action.get("path") or ""),
            str(action.get("name") or ""),
        )
        return inferred in cls._PRODUCT_FAMILIES
