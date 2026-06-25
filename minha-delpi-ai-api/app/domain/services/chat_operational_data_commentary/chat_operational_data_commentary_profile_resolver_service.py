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
_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentaryProfileResolverService:
    @classmethod
    def resolve_profile_key(cls,
        *,
        path: str = "",
        entity: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        meta = metadata if isinstance(metadata, dict) else {}
        stack_plan = meta.get("stackPresentationPlan")
        presentation_key = ""

        if isinstance(stack_plan, dict):
            presentation_key = str(stack_plan.get("presentationProfileKey") or "").strip()

        entity_token = str(entity or "").strip()

        if not entity_token:
            api_meta = meta.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                entity_token = str(api_meta.get("entity") or "").strip()

        if not presentation_key:
            presentation_key = ChatPresentationProfileService.resolve_profile_key(
                path,
                entity_token or None,
            )

        commentary_key = ChatPresentationProfileService.commentary_profile_key(
            presentation_key,
            path=path,
            entity=entity_token or None,
        )

        if commentary_key:
            return commentary_key

        return None

