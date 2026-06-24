"""Gate canônico — síntese LLM para overview e perfis summary_then_evidence.

Intenção narrativa e policies: este serviço.
Escolha template vs LLM vs direct no turno: ``ChatPresentationProseDeliveryService`` (playbook-18).
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_narrative_synthesis_content_service import (
    ChatOperationalNarrativeSynthesisContentService,
)
from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)
from app.domain.services.chat_product_overview_intent_service import (
    ChatProductOverviewIntentService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_SYNTHESIS_PRODUCT_OVERVIEW = "product_overview"
_SYNTHESIS_SUMMARY_THEN_EVIDENCE = "summary_then_evidence"
_SYNTHESIS_OPERATIONAL_DATA = "operational_data"
_SYNTHESIS_PLAYBOOK_DATA = "playbook_data"
_SYNTHESIS_KPI_DATA = "kpi_data"
_SYNTHESIS_SQL_RESULT = "sql_result"
_SYNTHESIS_ERROR_RECOVERY = "error_recovery"
_SYNTHESIS_STRUCTURE_EXCLUSIVITY = "structure_exclusivity"


class ChatOperationalNarrativeSynthesisService:
    @classmethod
    def resolve_synthesis_kind(
        cls,
        message: str | None,
        tool_calls: list | None = None,
    ) -> str | None:
        if ChatProductOverviewIntentService.is_product_overview_message(message):
            return _SYNTHESIS_PRODUCT_OVERVIEW

        if cls._qualifies_summary_then_evidence(message, tool_calls):
            return _SYNTHESIS_SUMMARY_THEN_EVIDENCE

        if cls._tool_calls_match_path_markers(tool_calls, cls._content().sql_path_markers()):
            return _SYNTHESIS_SQL_RESULT

        if cls._tool_calls_match_path_markers(
            tool_calls,
            cls._content().structure_exclusivity_path_markers(),
        ):
            return _SYNTHESIS_STRUCTURE_EXCLUSIVITY

        if cls._tool_calls_match_path_markers(
            tool_calls,
            cls._content().playbook_path_markers(),
        ) or cls._tool_calls_match_path_markers(
            tool_calls,
            cls._content().kpi_path_markers(),
        ):
            return _SYNTHESIS_OPERATIONAL_DATA

        if tool_calls is None and cls._message_suggests_summary_then_evidence(message):
            return _SYNTHESIS_SUMMARY_THEN_EVIDENCE

        from app.domain.services.chat_presentation_prose_delivery_content_service import (
            ChatPresentationProseDeliveryContentService,
        )
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if ChatPresentationProseDeliveryContentService.llm_prose_everywhere():
            if ChatPresentationProseDeliveryService._has_failed_external_action(tool_calls):
                return _SYNTHESIS_ERROR_RECOVERY

            if ChatPresentationProseDeliveryService._has_successful_external_action(tool_calls):
                return _SYNTHESIS_OPERATIONAL_DATA

        return None

    @classmethod
    def should_force_llm_synthesis(
        cls,
        message: str | None,
        tool_calls: list | None = None,
    ) -> bool:
        """Detecta intenção narrativa — preferir ``ChatPresentationProseDeliveryService`` no turno."""
        from app.domain.services.chat_presentation_prose_delivery_content_service import (
            ChatPresentationProseDeliveryContentService,
        )
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
            MODE_TEMPLATE,
        )

        if (
            ChatPresentationProseDeliveryContentService.llm_prose_everywhere()
            and ChatPresentationProseDeliveryService.llm_prose_globally_available()
        ):
            if (
                ChatPresentationProseDeliveryService._entity_prose_delivery_mode(
                    tool_calls=tool_calls,
                )
                == MODE_TEMPLATE
            ):
                return False

            if ChatPresentationProseDeliveryService._has_successful_external_action(
                tool_calls,
            ):
                return True

            if ChatPresentationProseDeliveryService._has_failed_external_action(tool_calls):
                return True

        kind = cls.resolve_synthesis_kind(message, tool_calls)

        if not kind:
            return False

        if kind == _SYNTHESIS_PRODUCT_OVERVIEW:
            return ChatProductOverviewIntentService.should_force_llm_synthesis(
                message,
                tool_calls,
            )

        return cls._has_successful_qualifying_tool(tool_calls)

    @classmethod
    def message_suggests_narrative_llm_synthesis(cls, message: str | None) -> bool:
        """Heurística só com a mensagem — usada no pipeline antes das tools."""
        if cls._message_suggests_summary_then_evidence(message):
            return True

        kind = cls.resolve_synthesis_kind(message, None)

        if not kind:
            return False

        if kind == _SYNTHESIS_PRODUCT_OVERVIEW:
            return ChatProductOverviewIntentService.is_product_overview_message(message)

        return not cls._looks_factual_narrow(message)

    @classmethod
    def build_prompt_policy_addon(
        cls,
        message: str | None,
        *,
        response_mode: str | None = None,
        tool_calls: list | None = None,
    ) -> str:
        kind = cls.resolve_synthesis_kind(message, tool_calls)

        if not kind:
            from app.domain.services.chat_presentation_prose_delivery_content_service import (
                ChatPresentationProseDeliveryContentService,
            )
            from app.domain.services.chat_presentation_prose_delivery_service import (
                ChatPresentationProseDeliveryService,
            )

            if (
                ChatPresentationProseDeliveryContentService.llm_prose_everywhere()
                and ChatPresentationProseDeliveryService.llm_prose_globally_available()
            ):
                if ChatPresentationProseDeliveryService._has_failed_external_action(
                    tool_calls,
                ):
                    kind = _SYNTHESIS_ERROR_RECOVERY
                elif ChatPresentationProseDeliveryService._has_successful_external_action(
                    tool_calls,
                ):
                    kind = kind or _SYNTHESIS_OPERATIONAL_DATA

        if not kind:
            return ""

        from app.domain.services.chat_operational_llm_synthesis_context_service import (
            ChatOperationalLlmSynthesisContextService,
        )
        from app.domain.services.chat_response_mode_service import ChatResponseModeService
        from app.domain.services.prompt_policy_service import PromptPolicyService

        normalized = ChatResponseModeService.normalize(response_mode)
        policy_kind = cls._resolve_policy_kind(kind, tool_calls)
        policy_name = ChatOperationalNarrativeSynthesisContentService.synthesis_policy(
            policy_kind,
            normalized,
        )

        if not policy_name:
            return ""

        policy = PromptPolicyService()._load_policy(policy_name)
        addon = f"\n\n{policy}" if policy else ""
        facts = ChatOperationalLlmSynthesisContextService.build_facts_addon(
            tool_calls,
            response_mode=response_mode,
        )

        return f"{addon}{facts}"

    @classmethod
    def is_llm_synthesis_effect(cls, effect: str | None) -> bool:
        normalized = str(effect or "").strip()

        return normalized in {"llm_synthesis", "llm_synthesis_brief"}

    @classmethod
    def _qualifies_summary_then_evidence(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if cls._looks_factual_narrow(message):
            return False

        return cls._has_successful_qualifying_tool(tool_calls)

    @classmethod
    def _looks_factual_narrow(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(term in normalized for term in cls._content().factual_narrow_terms()):
            return False

        return not any(marker in normalized for marker in cls._content().narrative_markers())

    @classmethod
    def _message_suggests_summary_then_evidence(cls, message: str | None) -> bool:
        if cls._looks_factual_narrow(message):
            return False

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not ChatProductQueryIntentService.extract_product_code(message or ""):
            return False

        if ChatProductQueryIntentService._looks_like_factory_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_production_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_shipping_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return any(marker in normalized for marker in cls._content().narrative_markers())

        return False

    @classmethod
    def _has_successful_qualifying_tool(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if cls._metadata_qualifies(metadata):
                return True

        return False

    @classmethod
    def _metadata_qualifies(cls, metadata: dict[str, Any]) -> bool:
        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            return True

        if not ChatRichPresentationTextService.is_stack_layout(metadata):
            return False

        profile_key = cls._resolve_profile_key(metadata)

        if profile_key and profile_key in cls._content().evidence_first_profile_keys():
            return True

        path = str(metadata.get("path") or "").lower()

        return any(marker in path for marker in cls._content().path_markers())

    @classmethod
    def _resolve_profile_key(cls, metadata: dict[str, Any]) -> str | None:
        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            profile_key = str(data_answer.get("profileKey") or "").strip()

            if profile_key:
                return profile_key

        for plan_key in ("stackPresentationPlan",):
            plan = metadata.get(plan_key)

            if not isinstance(plan, dict):
                continue

            presentation_profile = str(plan.get("presentationProfile") or "").strip()

            if presentation_profile:
                mapped = cls._content().entity_profile_map().get(presentation_profile)

                if mapped:
                    return mapped

            profile_key = str(plan.get("presentationProfileKey") or "").strip()

            if profile_key in cls._content().evidence_first_profile_keys():
                return profile_key

        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            entity = str(api_meta.get("entity") or "").strip()
            mapped = cls._content().entity_profile_map().get(entity)

            if mapped:
                return mapped

        return None

    @classmethod
    def _resolve_policy_kind(cls, kind: str, tool_calls: list | None) -> str:
        if kind == _SYNTHESIS_OPERATIONAL_DATA:
            if cls._tool_calls_match_path_markers(
                tool_calls,
                cls._content().structure_exclusivity_path_markers(),
            ):
                return _SYNTHESIS_STRUCTURE_EXCLUSIVITY

            if cls._tool_calls_match_path_markers(
                tool_calls,
                cls._content().kpi_path_markers(),
            ):
                return _SYNTHESIS_KPI_DATA

            return _SYNTHESIS_PLAYBOOK_DATA

        return kind

    @classmethod
    def _tool_calls_match_path_markers(
        cls,
        tool_calls: list | None,
        markers: tuple[str, ...],
    ) -> bool:
        if not isinstance(tool_calls, list) or not markers:
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").lower()

            if any(marker in path for marker in markers):
                return True

        return False

    @classmethod
    def _content(cls) -> type[ChatOperationalNarrativeSynthesisContentService]:
        return ChatOperationalNarrativeSynthesisContentService
