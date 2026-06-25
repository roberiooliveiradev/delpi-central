"""Delegate — comentário operacional."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_constants import (
    CONTENT_SECTION as _CONTENT_SECTION,
    MP_LOW_COVERAGE_PA_THRESHOLD as _MP_LOW_COVERAGE_PA_THRESHOLD,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_facade_access import (
    commentary_service,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentaryMiscService:
    @classmethod
    def _build_sale_pricing_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        _ = format_quantity

        from app.domain.services.chat_product_pricing_insight_service import (
            ChatProductPricingInsightService,
        )

        return ChatProductPricingInsightService.build_commentary(root)

    @classmethod
    def _build_analyser_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        _ = format_quantity

        from app.domain.services.chat_product_analyser_divergence_service import (
            ChatProductAnalyserDivergenceService,
        )

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        highlights: list[str] = []
        attention = ChatProductAnalyserDivergenceService.build_attention_points(root, product)
        opening = ChatProductAnalyserDivergenceService.build_opening_narrative(root, product)

        if opening:
            highlights.append(opening)

        if not highlights and not attention:
            return {}

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "alertLevel": "attention" if attention else "ok",
        }

