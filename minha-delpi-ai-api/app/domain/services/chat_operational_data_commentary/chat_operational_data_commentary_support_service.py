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
_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentarySupportService:
    @staticmethod
    def _presenter_format(section: str, key: str, **values: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return ChatAssistantContentService.format(
            "presenter_content",
            "routePresentations",
            section,
            key,
            **values,
        )

    @classmethod
    def _build_narrative_insight(cls, commentary: dict[str, Any]) -> str:
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

        if not highlights and not attention:
            return ""

        lead = highlights[0] if highlights else attention[0]
        extras = highlights[1:3] if len(highlights) > 1 else []

        if attention and not extras:
            extras = attention[:2]

        body = " ".join(extras)

        if body:
            return f"{lead} {body}".strip()

        return lead

    @classmethod
    def _section_block(cls, root: dict[str, Any], key: str) -> dict[str, Any]:
        block = root.get(key)

        if isinstance(block, dict):
            return block

        return {}

    @classmethod
    def _content_profile(cls, profile_key: str) -> str:
        return ChatOperationalCommentaryProfileService.content_section(profile_key)

    @classmethod
    def _text(cls, profile: str, key: str, **values: str) -> str:
        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                _CONTENT_SECTION,
                profile,
                key,
                **values,
            )

        return ChatAssistantContentService.get(
            "presenter_content",
            _CONTENT_SECTION,
            profile,
            key,
            default="",
        )

