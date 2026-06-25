"""Delegate — parâmetros operacionais."""

from __future__ import annotations

from datetime import date

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_constants import (
    INTENTS_REQUIRING_CODE,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_facade_access import (
    operational_parameter_service,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_types import (
    _parameter_content,
)



class ChatOperationalParameterDateService:
    @classmethod
    def resolve_missing_date_answer(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        from app.domain.services.chat_operational_date_parameter_service import (
            ChatOperationalDateParameterService,
        )

        return ChatOperationalDateParameterService.resolve_missing_date_answer(
            message,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            conversation_context=conversation_context,
        )

    @classmethod
    def should_skip_tools_for_missing_date(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> bool:
        return operational_parameter_service().resolve_missing_date_answer(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        ) is not None

