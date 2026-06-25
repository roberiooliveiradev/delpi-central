"""Perfis declarativos de apresentação — fachada fina (W3)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_contract_service import (
    ChatPresentationProfileContractService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_decision_service import (
    ChatPresentationProfileDecisionService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_entity_service import (
    ChatPresentationProfileEntityService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_flags_service import (
    ChatPresentationProfileFlagsService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_openapi_service import (
    ChatPresentationProfileOpenApiService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_path_service import (
    ChatPresentationProfilePathService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_prose_service import (
    ChatPresentationProfileProseService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_resolve_service import (
    ChatPresentationProfileResolveService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_stack_service import (
    ChatPresentationProfileStackService,
)


class ChatPresentationProfileService(ChatAssistantVocabularyService):
    """Fachada — vocabulário `presentation_profiles` + resolução de perfil por rota/entidade."""

    BUNDLE = "presentation_profiles"

    _SESSION_FORMAT_ALIASES = {
        "topics": "text",
    }

    @classmethod
    def entity_set(cls, set_key: str) -> frozenset[str]:
        return ChatPresentationProfileEntityService.entity_set(set_key)

    @classmethod
    def is_enriched_openapi_presentation(
        cls,
        *,
        delpi_metadata: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> bool:
        return ChatPresentationProfileOpenApiService.is_enriched_openapi_presentation(
            delpi_metadata=delpi_metadata,
            profile=profile,
        )

    @classmethod
    def allows_automatic_rich_stack(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return ChatPresentationProfileOpenApiService.allows_automatic_rich_stack(
            path=path,
            entity=entity,
            delpi_metadata=delpi_metadata,
            metadata=metadata,
        )

    @classmethod
    def uses_schema_first_presentation(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> bool:
        return ChatPresentationProfileOpenApiService.uses_schema_first_presentation(
            path, entity
        )

    @classmethod
    def is_rich_stack_profile(cls, profile_key: str | None) -> bool:
        return ChatPresentationProfileOpenApiService.is_rich_stack_profile(profile_key)

    @classmethod
    def uses_presentation_table_assembly(cls, entity: str | None) -> bool:
        return ChatPresentationProfileOpenApiService.uses_presentation_table_assembly(entity)

    @classmethod
    def entity_routed_for_present(cls) -> frozenset[str]:
        return ChatPresentationProfileEntityService.entity_routed_for_present()

    @classmethod
    def entity_presentation_routing(cls) -> dict[str, Any]:
        return ChatPresentationProfileEntityService.entity_presentation_routing()

    @classmethod
    def prose_delivery_mode(
        cls,
        *,
        entity: str | None = None,
        path: str | None = None,
    ) -> str | None:
        return ChatPresentationProfileProseService.prose_delivery_mode(
            entity=entity,
            path=path,
        )

    @classmethod
    def operational_empty_route_key(cls, entity: str | None) -> str | None:
        return ChatPresentationProfileEntityService.operational_empty_route_key(entity)

    @classmethod
    def is_product_operational_entity(cls, entity: str | None) -> bool:
        return ChatPresentationProfileEntityService.is_product_operational_entity(entity)

    @classmethod
    def list_route_entity(cls, entity: str | None) -> str | None:
        return ChatPresentationProfileEntityService.list_route_entity(entity)

    @classmethod
    def is_no_chart_entity(cls, entity: str | None) -> bool:
        return ChatPresentationProfileEntityService.is_no_chart_entity(entity)

    @classmethod
    def entity_set_profile_contracts(cls) -> dict[str, dict[str, Any]]:
        return ChatPresentationProfileContractService.entity_set_profile_contracts()

    @classmethod
    def resolve_profile_contract(
        cls,
        entity: str | None,
        *,
        path: str | None = None,
    ) -> dict[str, Any] | None:
        return ChatPresentationProfileContractService.resolve_profile_contract(
            entity,
            path=path,
        )

    @classmethod
    def entity_path_hints(cls) -> dict[str, str]:
        return ChatPresentationProfilePathService.entity_path_hints()

    @classmethod
    def entity_path_hint_pairs(cls) -> list[tuple[str, str]]:
        return ChatPresentationProfilePathService.entity_path_hint_pairs()

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        return ChatPresentationProfilePathService.entity_path_hint(entity)

    @classmethod
    def path_entity_fallbacks(cls) -> tuple[tuple[str, str], ...]:
        return ChatPresentationProfilePathService.path_entity_fallbacks()

    @classmethod
    def resolve_entity_from_path(cls, path: str | None) -> str | None:
        return ChatPresentationProfilePathService.resolve_entity_from_path(path)

    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        return ChatPresentationProfilePathService.path_lowered(path)

    @classmethod
    def resolve_profile_key(cls, path: str | None, entity: str | None = None) -> str:
        return ChatPresentationProfileResolveService.resolve_profile_key(path, entity)

    @classmethod
    def commentary_profile_key(
        cls,
        profile_key: str | None = None,
        *,
        path: str | None = None,
        entity: str | None = None,
    ) -> str | None:
        return ChatPresentationProfileResolveService.commentary_profile_key(
            profile_key,
            path=path,
            entity=entity,
        )

    @classmethod
    def profile(cls, profile_key: str | None = None) -> dict[str, Any]:
        return ChatPresentationProfileResolveService.profile(profile_key)

    @classmethod
    def resolve_profile(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileResolveService.resolve_profile(
            path,
            entity,
            shape=shape,
            delpi_metadata=delpi_metadata,
            metadata=metadata,
        )

    @classmethod
    def build_resolved_profile(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileResolveService.build_resolved_profile(
            path=path,
            entity=entity,
            shape=shape,
            delpi_metadata=delpi_metadata,
        )

    @classmethod
    def cache_presentation_profile(cls, metadata: dict[str, Any]) -> None:
        return ChatPresentationProfileResolveService.cache_presentation_profile(metadata)

    @classmethod
    def resolve_effective_profile_key(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        operation_id: str | None = None,
    ) -> str:
        return ChatPresentationProfileResolveService.resolve_effective_profile_key(
            path,
            entity,
            shape=shape,
            operation_id=operation_id,
        )

    @classmethod
    def flags(cls, path: str | None, entity: str | None = None) -> frozenset[str]:
        return ChatPresentationProfileFlagsService.flags(path, entity)

    @classmethod
    def has_flag(
        cls,
        path: str | None,
        flag: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return ChatPresentationProfileFlagsService.has_flag(path, flag, entity=entity)

    @classmethod
    def stack_plan_config(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        presentation_mode: str | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileStackService.stack_plan_config(
            path,
            entity,
            presentation_mode=presentation_mode,
        )

    @classmethod
    def stack_plan_config_for_evidence_first(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileStackService.stack_plan_config_for_evidence_first(
            path, entity
        )

    @classmethod
    def presentation_decision_config(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileDecisionService.presentation_decision_config(
            path, entity
        )

    @classmethod
    def resolve_default_preferred_format(
        cls,
        *,
        path: str | None,
        session_format: str | None = None,
        entity: str | None = None,
        has_tree: bool = False,
        has_table: bool = False,
        has_chart: bool = False,
        has_text: bool = False,
        has_kpi: bool = False,
    ) -> str | None:
        return ChatPresentationProfileDecisionService.resolve_default_preferred_format(
            path=path,
            session_format=session_format,
            entity=entity,
            has_tree=has_tree,
            has_table=has_table,
            has_chart=has_chart,
            has_text=has_text,
            has_kpi=has_kpi,
        )

    @classmethod
    def apply_visual_order(
        cls,
        decision: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        return ChatPresentationProfileDecisionService.apply_visual_order(
            decision,
            path=path,
            entity=entity,
            metadata=metadata,
        )

    @classmethod
    def humanized_narrative_mode(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> str:
        return ChatPresentationProfileDecisionService.humanized_narrative_mode(path, entity)

    @classmethod
    def data_answer_lead_alignment(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> str:
        return ChatPresentationProfileDecisionService.data_answer_lead_alignment(path, entity)

    @classmethod
    def should_auto_force_chart(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        has_tree: bool = False,
        has_chart: bool = False,
    ) -> bool:
        return ChatPresentationProfileDecisionService.should_auto_force_chart(
            path,
            entity,
            has_tree=has_tree,
            has_chart=has_chart,
        )

    # --- Delegates privados ---

    @classmethod
    def _stamp_openapi_presentation_strategy(
        cls,
        profile: dict[str, Any],
        delpi_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileOpenApiService._stamp_openapi_presentation_strategy(
            profile,
            delpi_metadata,
        )

    @classmethod
    def _path_rule_suppressed(cls, fragment: str, lowered_path: str) -> bool:
        return ChatPresentationProfileResolveService._path_rule_suppressed(
            fragment, lowered_path
        )

    @classmethod
    def _matches_product_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        return ChatPresentationProfilePathService._matches_product_path_hint(
            path_lower, hint_lower
        )

    @classmethod
    def _matches_quality_action_plan_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        return ChatPresentationProfilePathService._matches_quality_action_plan_path_hint(
            path_lower, hint_lower
        )

    @classmethod
    def _matches_entity_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        return ChatPresentationProfilePathService._matches_entity_path_hint(
            path_lower, hint_lower
        )

    @classmethod
    def _resolve_quality_action_plan_entity_from_path(cls, lowered: str) -> str | None:
        return ChatPresentationProfilePathService._resolve_quality_action_plan_entity_from_path(
            lowered
        )

    @classmethod
    def _generic_default_preferred_format(
        cls,
        *,
        has_tree: bool,
        has_table: bool,
        has_chart: bool,
        has_text: bool,
        has_kpi: bool,
    ) -> str | None:
        return ChatPresentationProfileDecisionService._generic_default_preferred_format(
            has_tree=has_tree,
            has_table=has_table,
            has_chart=has_chart,
            has_text=has_text,
            has_kpi=has_kpi,
        )
