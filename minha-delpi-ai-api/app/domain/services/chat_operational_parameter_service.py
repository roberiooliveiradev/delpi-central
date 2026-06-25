"""Parâmetros obrigatórios em consultas operacionais — fachada fina (W3)."""

from __future__ import annotations

from datetime import date

from app.domain.services.chat_operational_parameter.chat_operational_parameter_constants import (
    INTENTS_REQUIRING_CODE,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_date_service import (
    ChatOperationalParameterDateService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_period_service import (
    ChatOperationalParameterPeriodService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_product_code_service import (
    ChatOperationalParameterProductCodeService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_tool_skip_service import (
    ChatOperationalParameterToolSkipService,
)


class ChatOperationalParameterService:
    """Detecta consultas operacionais incompletas e evita tools/LLM desnecessários."""

    _INTENTS_REQUIRING_CODE = INTENTS_REQUIRING_CODE

    @classmethod
    def resolve_missing_product_code_answer(cls, *args, **kwargs) -> str | None:
        return ChatOperationalParameterProductCodeService.resolve_missing_product_code_answer(
            *args, **kwargs
        )

    @classmethod
    def should_skip_tools(cls, *args, **kwargs) -> bool:
        return ChatOperationalParameterToolSkipService.should_skip_tools(*args, **kwargs)

    @classmethod
    def should_skip_agentic_loop(cls, *args, **kwargs) -> bool:
        return ChatOperationalParameterToolSkipService.should_skip_agentic_loop(*args, **kwargs)

    @classmethod
    def should_block_semantic_action_fallback(cls, *args, **kwargs) -> bool:
        return ChatOperationalParameterToolSkipService.should_block_semantic_action_fallback(
            *args, **kwargs
        )

    @classmethod
    def resolve_ambiguous_period_answer(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
        today: date | None = None,
    ) -> str | None:
        return ChatOperationalParameterPeriodService.resolve_ambiguous_period_answer(
            message,
            previous_messages=previous_messages,
            today=today,
        )

    @classmethod
    def should_skip_tools_for_ambiguous_period(cls, *args, **kwargs) -> bool:
        return ChatOperationalParameterPeriodService.should_skip_tools_for_ambiguous_period(
            *args, **kwargs
        )

    @classmethod
    def resolve_missing_date_answer(cls, *args, **kwargs) -> str | None:
        return ChatOperationalParameterDateService.resolve_missing_date_answer(*args, **kwargs)

    @classmethod
    def should_skip_tools_for_missing_date(cls, *args, **kwargs) -> bool:
        return ChatOperationalParameterDateService.should_skip_tools_for_missing_date(
            *args, **kwargs
        )

    # --- Delegates privados ---

    @classmethod
    def _product_context_terms(cls) -> tuple[str, ...]:
        return ChatOperationalParameterProductCodeService._product_context_terms()

    @classmethod
    def _missing_product_code_intent(cls, *args, **kwargs) -> str | None:
        return ChatOperationalParameterProductCodeService._missing_product_code_intent(
            *args, **kwargs
        )

    @classmethod
    def _playbook_missing_product_code_sub_intent(cls, normalized: str) -> str | None:
        return ChatOperationalParameterProductCodeService._playbook_missing_product_code_sub_intent(
            normalized
        )

    @classmethod
    def _requires_explicit_product_context(cls, normalized: str, intent: str) -> bool:
        return ChatOperationalParameterProductCodeService._requires_explicit_product_context(
            normalized, intent
        )
