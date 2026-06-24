"""Gate canônico — escolha e aplicação de prosa template vs LLM vs direct."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_commentary_lead_service import (
    ChatOperationalCommentaryLeadService,
)
from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_prose_delivery_content_service import (
    ChatPresentationProseDeliveryContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

MODE_TEMPLATE = "template"
MODE_LLM = "llm"
MODE_DIRECT = "direct"


class ChatPresentationProseDeliveryService:
    @classmethod
    def resolve_mode(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        del response_mode

        entity_mode = cls._entity_prose_delivery_mode(tool_calls=tool_calls)

        if entity_mode == MODE_TEMPLATE:
            return MODE_TEMPLATE

        if entity_mode == MODE_DIRECT:
            return MODE_DIRECT

        if (
            ChatPresentationProseDeliveryContentService.llm_prose_everywhere()
            and cls.llm_prose_globally_available()
        ):
            if cls._has_successful_external_action(tool_calls):
                return MODE_LLM

            if cls._has_failed_external_action(tool_calls):
                return MODE_LLM

        if cls._qualifies_llm_prose(message, tool_calls):
            return MODE_LLM

        if cls._qualifies_direct_prose(message, tool_calls):
            return MODE_DIRECT

        if cls.template_prose_allowed():
            return MODE_TEMPLATE

        return cls._resolve_non_template_mode(message, tool_calls)

    @classmethod
    def template_prose_allowed(cls) -> bool:
        """P8.1 — prosa template só em rollback offline (modos OFF + flag JSON)."""
        if ChatPresentationProseDeliveryContentService.llm_prose_everywhere():
            return False

        if ChatPresentationProseDeliveryContentService.deprecate_humanized_linhas_as_prose():
            return False

        if not ChatPresentationProseDeliveryContentService.allow_template_prose_fallback():
            return False

        if ChatResponseModeService.is_enabled():
            return False

        return True

    @classmethod
    def _resolve_non_template_mode(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> str:
        if cls._qualifies_llm_prose(message, tool_calls):
            return MODE_LLM

        if cls._qualifies_direct_prose(message, tool_calls):
            return MODE_DIRECT

        if cls.llm_prose_globally_available():
            return MODE_LLM

        if cls._has_successful_external_action(tool_calls) or cls._has_failed_external_action(
            tool_calls,
        ):
            return MODE_LLM

        return MODE_DIRECT

    @classmethod
    def _has_successful_external_action(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return True

        return False

    @classmethod
    def _has_failed_external_action(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok") is False:
                return True

        return False

    @classmethod
    def apply_turn(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        mode = cls.resolve_mode(message, tool_calls, response_mode=response_mode)

        if not isinstance(tool_calls, list):
            return mode

        if mode == MODE_LLM:
            from app.domain.services.chat_presentation_llm_prose_decoupling_service import (
                ChatPresentationLlmProseDecouplingService,
            )

            ChatPresentationLlmProseDecouplingService.apply_to_tool_calls(
                tool_calls,
                message=message,
            )

        cls._stamp_delivery_mode(tool_calls, mode)
        return mode

    @classmethod
    def apply_to_tool_context_result(
        cls,
        tool_context: dict[str, Any] | None,
        message: str | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        """Aplica o gate canônico ao payload de tool context (send, stream, simulate, preview)."""
        if not isinstance(tool_context, dict):
            return MODE_TEMPLATE

        tool_calls = tool_context.get("toolCalls")

        if not isinstance(tool_calls, list) or not tool_calls:
            return MODE_TEMPLATE

        return cls.apply_turn(
            message,
            tool_calls,
            response_mode=response_mode,
        )

    @classmethod
    def should_use_llm_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> bool:
        return (
            cls.resolve_mode(message, tool_calls, response_mode=response_mode) == MODE_LLM
        )

    @classmethod
    def should_use_template_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> bool:
        return (
            cls.resolve_mode(message, tool_calls, response_mode=response_mode)
            == MODE_TEMPLATE
        )

    @classmethod
    def is_llm_decoupled_metadata(cls, metadata: dict[str, Any] | None) -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get("llmProseDecoupled"):
            return True

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            prose_source = str(decision.get("proseSource") or "").strip().lower()

            if prose_source == MODE_LLM:
                return True

        return str(metadata.get("proseDeliveryMode") or "").strip().lower() == MODE_LLM

    @classmethod
    def resolve_effective_humanized_summary(
        cls,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Humanized visível para fatos/follow-up — usa archive quando prosa LLM limpou linhas."""
        if not isinstance(metadata, dict):
            return None

        humanized = metadata.get("humanizedSummary")
        effective: dict[str, Any] = dict(humanized) if isinstance(humanized, dict) else {}

        lines = [
            str(line).strip()
            for line in (effective.get("linhas") or [])
            if str(line or "").strip()
        ]

        if not lines and cls.is_llm_decoupled_metadata(metadata):
            archive = metadata.get("templateProseArchive")

            if isinstance(archive, dict):
                archived = archive.get("humanizedSummary")

                if isinstance(archived, dict):
                    if not str(effective.get("titulo") or "").strip():
                        title = archived.get("titulo")

                        if title not in (None, ""):
                            effective["titulo"] = title

                    lines = [
                        str(line).strip()
                        for line in (archived.get("linhas") or [])
                        if str(line or "").strip()
                    ]

        if lines:
            effective["linhas"] = lines
        elif "linhas" in effective:
            effective["linhas"] = []

        title = str(effective.get("titulo") or "").strip()

        if not title and not lines:
            return None

        return effective

    @classmethod
    def should_block_template_prose_metadata(cls, metadata: dict[str, Any] | None) -> bool:
        if not isinstance(metadata, dict):
            return False

        if cls.is_llm_decoupled_metadata(metadata):
            return True

        from app.domain.services.chat_presentation_data_only_prose_service import (
            ChatPresentationDataOnlyProseService,
        )

        return ChatPresentationDataOnlyProseService.is_data_only_metadata(metadata)

    @classmethod
    def resolve_humanized_lines_for_display(
        cls,
        metadata: dict[str, Any] | None,
    ) -> list[str]:
        if cls.should_block_template_prose_metadata(metadata):
            return []

        if not isinstance(metadata, dict):
            return []

        humanized = metadata.get("humanizedSummary")

        if not isinstance(humanized, dict):
            return []

        return [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]

    @classmethod
    def resolve_humanized_detail_lines_for_display(
        cls,
        metadata: dict[str, Any] | None,
    ) -> list[str]:
        if cls.should_block_template_prose_metadata(metadata):
            return []

        if not isinstance(metadata, dict):
            return []

        humanized = metadata.get("humanizedSummary")

        if not isinstance(humanized, dict):
            return []

        return [
            str(line).strip()
            for line in (humanized.get("linhas_detalhe") or [])
            if str(line or "").strip()
        ]

    @classmethod
    def resolve_humanized_lines_for_facts(
        cls,
        metadata: dict[str, Any] | None,
    ) -> list[str]:
        effective = cls.resolve_effective_humanized_summary(metadata)

        if not isinstance(effective, dict):
            return []

        return [
            str(line).strip()
            for line in (effective.get("linhas") or [])
            if str(line or "").strip()
        ]

    @classmethod
    def llm_prose_globally_available(cls) -> bool:
        """P3.1 — LLM narrativo disponível mesmo sem seletor de modos quando JSON permite."""
        if ChatResponseModeService.is_enabled():
            return True

        return not ChatPresentationProseDeliveryContentService.require_response_modes_for_llm_prose()

    @classmethod
    def should_skip_template_prose_in_pipeline(
        cls,
        user_message: str | None,
        *,
        path: str | None = None,
    ) -> bool:
        if not cls.llm_prose_globally_available():
            return False

        if cls._entity_prose_delivery_mode(path=path) == MODE_TEMPLATE:
            return False

        if ChatPresentationProseDeliveryContentService.llm_prose_everywhere():
            return bool(str(path or "").strip())

        if ChatPresentationProseDeliveryContentService.deprecate_humanized_linhas_as_prose():
            return bool(str(path or "").strip())

        message = str(user_message or "").strip()

        if not message:
            return False

        return ChatOperationalNarrativeSynthesisService.message_suggests_narrative_llm_synthesis(
            message,
        )

    @classmethod
    def _qualifies_llm_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if not ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
            message,
            tool_calls,
        ):
            return False

        if cls._entity_prose_delivery_mode(tool_calls=tool_calls) == MODE_TEMPLATE:
            return False

        return cls.llm_prose_globally_available()

    @classmethod
    def _entity_prose_delivery_mode(
        cls,
        *,
        path: str | None = None,
        tool_calls: list | None = None,
    ) -> str | None:
        entity = cls._resolve_entity_from_context(tool_calls, path)

        return ChatPresentationProfileService.prose_delivery_mode(
            entity=entity,
            path=path,
        )

    @classmethod
    def _resolve_entity_from_context(
        cls,
        tool_calls: list | None,
        path: str | None,
    ) -> str | None:
        if isinstance(tool_calls, list):
            for tool_call in tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                api_meta = metadata.get("apiDelpiResponseMeta")

                if isinstance(api_meta, dict):
                    entity = str(api_meta.get("entity") or "").strip()

                    if entity:
                        return entity

        return ChatPresentationProfileService.resolve_entity_from_path(path)

    @classmethod
    def _qualifies_direct_prose(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if ChatPresentationProseDeliveryContentService.llm_prose_everywhere():
            return False

        if not isinstance(tool_calls, list):
            return False

        if ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
            message,
            tool_calls,
        ):
            return False

        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )
        from app.domain.services.chat_operational_narrative_synthesis_content_service import (
            ChatOperationalNarrativeSynthesisContentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(
            term in normalized
            for term in ChatOperationalNarrativeSynthesisContentService.factual_narrow_terms()
        ):
            return False

        if any(
            marker in normalized
            for marker in ChatOperationalNarrativeSynthesisContentService.narrative_markers()
        ):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return True

        return False

    @classmethod
    def _stamp_delivery_mode(cls, tool_calls: list, mode: str) -> None:
        key = ChatPresentationProseDeliveryContentService.metadata_key("deliveryMode")

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            metadata[key] = mode

    @classmethod
    def resolve_llm_synthesis_answer_fallback(
        cls,
        answer: str | None,
        tool_calls: list | None,
        *,
        compact: bool = False,
        commentary_depth: str | None = None,
    ) -> str:
        """Quando síntese LLM falha ou retorna vazio, usa dataCommentary como lead."""
        body = str(answer or "").strip()
        min_chars = ChatPresentationProseDeliveryContentService.llm_synthesis_answer_fallback_min_chars()

        if len(body) >= min_chars:
            return body

        if not isinstance(tool_calls, list):
            return body

        from app.domain.services.chat_humanized_data_response_service import (
            ChatHumanizedDataResponseService,
        )

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if not cls.is_llm_decoupled_metadata(metadata):
                continue

            commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(
                metadata,
            )
            fallback = cls._format_data_commentary_lead(
                commentary,
                compact=compact,
                depth=commentary_depth,
            )

            if fallback:
                return fallback

        return body

    @classmethod
    def _format_data_commentary_lead(
        cls,
        commentary: dict[str, Any] | None,
        *,
        compact: bool = False,
        depth: str | None = None,
    ) -> str:
        return ChatOperationalCommentaryLeadService.format_lead(
            commentary,
            compact=compact,
            depth=depth,
        )

    @classmethod
    def finalize_llm_synthesis_answer(
        cls,
        answer: str | None,
        tool_calls: list | None,
        *,
        message: str | None = None,
        response_mode_effect: str | None = None,
        response_mode: str | None = None,
    ) -> str:
        """Fallback de prosa vazia + enriquecimento canônico (código, fidelidade, brevidade)."""
        from app.domain.services.chat_operational_llm_synthesis_turn_finalization_service import (
            ChatOperationalLlmSynthesisTurnFinalizationService,
        )
        from app.infrastructure.llm.llm_request_context import get_active_config

        resolved_mode = response_mode or get_active_config().response_mode

        return ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
            answer,
            tool_calls,
            message=message,
            response_mode=resolved_mode,
            response_mode_effect=response_mode_effect,
        )

    @classmethod
    def ensure_product_code_in_synthesis_prose(
        cls,
        answer: str | None,
        message: str | None,
        tool_calls: list | None,
    ) -> str:
        body = str(answer or "").strip()

        if not body:
            return body

        product_code = cls._resolve_synthesis_product_code(message, tool_calls)

        if not product_code:
            return body

        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(body)

        if product_code in normalized:
            return body

        prefix_template = ChatPresentationProseDeliveryContentService.product_code_lead_prefix()
        prefix = prefix_template.format(productCode=product_code)

        return f"{prefix}{body}".strip()

    @classmethod
    def _resolve_synthesis_product_code(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> str | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        code = ChatProductQueryIntentService.extract_product_code(message or "")

        if code:
            return code

        if not isinstance(tool_calls, list):
            return None

        import re

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "")
            match = re.search(r"/products/(\d{4,})/", path)

            if match:
                return ChatProductQueryIntentService.normalize_product_code(match.group(1))

        return None
