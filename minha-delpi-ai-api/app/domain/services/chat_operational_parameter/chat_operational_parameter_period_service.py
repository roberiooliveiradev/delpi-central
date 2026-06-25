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



class ChatOperationalParameterPeriodService:
    @classmethod
    def resolve_ambiguous_period_answer(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
        today: date | None = None,
    ) -> str | None:
        from datetime import date as date_cls

        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        reference = today or date_cls.today()

        if ChatDateRangeIntentService.is_year_clarification_reply(
            message,
            previous_messages,
        ):
            return None

        if not ChatDateRangeIntentService.looks_like_period_metric_question(message):
            return None

        ambiguous = ChatDateRangeIntentService.detect_ambiguous_named_month(
            message,
            today=reference,
        )

        if not ambiguous:
            return None

        template = (_parameter_content().get("ambiguousPeriodYear") or "").strip()

        if template:
            return template.format(
                month_label=ambiguous.month_label,
                current_year=ambiguous.current_year,
                previous_year=ambiguous.previous_year,
            )

        return ChatDateRangeIntentService.build_ambiguity_clarification(
            message,
            today=reference,
        )

    @classmethod
    def should_skip_tools_for_ambiguous_period(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        return operational_parameter_service().resolve_ambiguous_period_answer(
            message,
            previous_messages=previous_messages,
        ) is not None

