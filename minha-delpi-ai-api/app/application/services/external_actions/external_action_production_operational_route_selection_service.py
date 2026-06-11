"""Seleção determinística das rotas operacionais Playbook 15 Fase 1."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductionOperationalRouteSelectionService:
    _REASON_KEYS = {
        ProductionOperationalIntentKind.CONSUMPTION: "productionConsumptionTopItems",
        ProductionOperationalIntentKind.CONSUMPTION_BY_WORK_CENTER: "productionConsumptionByWorkCenter",
        ProductionOperationalIntentKind.CONSUMPTION_VALIDATED: "productionConsumptionValidated",
        ProductionOperationalIntentKind.PURCHASES_RANKING: "purchasesTopProducts",
        ProductionOperationalIntentKind.LOSSES_TOP: "productionLossesTopMaterials",
        ProductionOperationalIntentKind.LOSSES_RECORDS: "productionLossesRecords",
        ProductionOperationalIntentKind.SCHEDULE_TODAY: "productionScheduleToday",
        ProductionOperationalIntentKind.ORDERS_OPEN: "productionOrdersOpen",
        ProductionOperationalIntentKind.ORDERS_FINISHED: "productionOrdersFinished",
        ProductionOperationalIntentKind.WORK_CENTER_SUMMARY: "productionWorkCenterOrderSummary",
    }

    def try_select(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        kind = ChatProductionOperationalIntentService.resolve(message)

        if not kind:
            return None

        path_token = ChatProductionOperationalIntentService.path_token_for(kind)

        if not path_token:
            return None

        candidates = self._load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

        for action in candidates:
            if str(action.get("method") or "").upper() != "GET":
                continue

            path = str(action.get("path") or "").lower()

            if path_token not in path:
                continue

            parameters = {}

            if build_date_branch_parameters:
                parameters = build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                )

            if kind in {
                ProductionOperationalIntentKind.LOSSES_TOP,
                ProductionOperationalIntentKind.LOSSES_RECORDS,
            }:
                loss_type = ChatProductionOperationalIntentService.infer_loss_type(
                    ChatMessageNormalizationService.normalize_for_matching(message)
                )

                if loss_type:
                    parameters["loss_type"] = loss_type

            if not parameters:
                parameters = {"limit": 10}

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": ExternalActionResponseContentService.get(
                    "selectionReasons",
                    self._REASON_KEYS[kind],
                ),
            }

        return None

    @staticmethod
    def _load_candidates(
        message: str,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable[..., list[dict]] | None,
    ) -> list[dict]:
        if not candidates_loader:
            return []

        return candidates_loader(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )
