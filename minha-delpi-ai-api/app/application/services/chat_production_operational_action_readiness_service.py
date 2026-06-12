"""Diagnóstico quando intent Playbook 15 bate mas nenhuma action é selecionada (Playbook 16 O5)."""

from __future__ import annotations

from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)


class ChatProductionOperationalActionReadinessService:
    @classmethod
    def resolve_gap_direct_answer(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str],
        repository,
        provider_key: str = "api-delpi",
    ) -> str | None:
        if not ChatProductionOperationalIntentService.matches_rest_route(message):
            return None

        kind = ChatProductionOperationalIntentService.resolve(message)

        if not kind:
            return None

        path_token = ChatProductionOperationalIntentService.path_token_for(kind)

        if not path_token:
            return None

        support = ExternalActionSelectionSupportService(repository)
        catalog_actions = support.find_catalog_actions_by_path_token(
            path_token=path_token,
            provider_key=provider_key,
        )

        path_label = path_token

        if not catalog_actions:
            return ChatTurnPreparationContentService.format(
                "directAnswers",
                "productionOperational",
                "actionMissingFromCatalog",
                pathLabel=path_label,
                providerKey=provider_key,
            )

        allowed = {str(item) for item in allowed_action_ids}
        enabled_matches = [
            action
            for action in catalog_actions
            if str(action.get("actionId")) in allowed
        ]

        if enabled_matches:
            return None

        sample = catalog_actions[0]
        action_id = str(sample.get("actionId") or sample.get("operationId") or path_label)

        return ChatTurnPreparationContentService.format(
            "directAnswers",
            "productionOperational",
            "actionNotEnabledOnAgent",
            pathLabel=path_label,
            actionId=action_id,
        )
