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
    PROFILE_CONTENT_MAP as _PROFILE_CONTENT_MAP,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_facade_access import (
    commentary_service,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentaryOrchestrationService:
    @classmethod
    def build(cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(data, dict) or not profile_key:
            return None

        builders = {
            "factory_status": commentary_service()._build_factory_commentary,
            "stock": commentary_service()._build_stock_commentary,
            "production_status": commentary_service()._build_production_commentary,
            "shipping_status": commentary_service()._build_shipping_commentary,
            "directives": commentary_service()._build_directives_commentary,
            "sale_pricing": commentary_service()._build_sale_pricing_commentary,
            "analyser": commentary_service()._build_analyser_commentary,
            "structure_exclusivity": commentary_service()._build_structure_exclusivity_commentary,
        }
        builder = builders.get(str(profile_key).strip())

        if not builder:
            return None

        metadata_only = ChatOperationalCommentaryProfileService.try_build_metadata_only(
            str(profile_key).strip(),
        )

        if metadata_only is not None:
            return metadata_only

        commentary = builder(data, format_quantity=format_quantity)

        if not commentary:
            return None

        if not (commentary.get("highlights") or commentary.get("attention")):
            return None

        commentary["profileKey"] = profile_key
        commentary["narrativeInsight"] = ChatOperationalDataCommentarySupportService._build_narrative_insight(commentary)

        return ChatHumanizedDataResponseService.normalize(commentary, profile_key=profile_key)

    @classmethod
    def render_markdown_sections(cls, commentary: dict[str, Any] | None) -> str:
        if not isinstance(commentary, dict):
            return ""

        parts: list[str] = []
        quick_layer = ChatHumanizedDataResponseService.render_quick_layer_markdown(commentary)

        if quick_layer:
            parts.append(quick_layer)

        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]
        profile_key = ChatOperationalDataCommentarySupportService._content_profile(str(commentary.get("profileKey") or "factory_status"))

        if highlights:
            parts.extend(
                [
                    "",
                    ChatOperationalDataCommentarySupportService._text(profile_key, "highlightsHeader"),
                    "",
                    *[f"- {line}" for line in highlights],
                ]
            )

        if attention:
            parts.extend(
                [
                    "",
                    ChatOperationalDataCommentarySupportService._text(profile_key, "attentionHeader"),
                    "",
                    *[f"{index}. {line}" for index, line in enumerate(attention, start=1)],
                ]
            )

        return _OpsTable.join_markdown_blocks(parts)

