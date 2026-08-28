"""Seleção genérica por ranking semântico — Fase 3B lote 19."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.application.services.external_actions.external_action_score_gap_clarification_service import (
    ExternalActionScoreGapClarificationService,
)
from app.application.services.external_actions.external_action_selection_diagnostics_service import (
    ExternalActionSelectionDiagnosticsService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionGenericRouteSelectionService:
    def select(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        if not allowed_action_ids or not candidates_loader or not rank_candidates:
            return None

        candidates = candidates_loader(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=120,
        )

        if not candidates:
            return None

        ranked = rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed_action_ids,
        )

        if not ranked:
            return None

        from app.application.services.external_actions.external_action_selection_read_policy_service import (
            ExternalActionSelectionReadPolicyService,
        )

        action, ranked, read_policy_reason = ExternalActionSelectionReadPolicyService.apply(
            ranked
        )

        if read_policy_reason == "readPolicyClarification":
            return ExternalActionSelectionDiagnosticsService.annotate(
                {
                    "name": ExternalActionScoreGapClarificationService.clarification_tool_name(),
                    "arguments": {
                        "message": ExternalActionResponseContentService.get(
                            "selectionReasons",
                            "readPolicyClarification",
                        ),
                    },
                    "reason": ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "readPolicyClarification",
                    ),
                    "directAnswer": ExternalActionResponseContentService.get(
                        "selectionReasons",
                        "readPolicyClarification",
                    ),
                },
                match_source="semanticFallback",
                ranked=ranked,
                reason_key="readPolicyClarification",
            )

        clarification = ExternalActionScoreGapClarificationService.maybe_build(ranked)
        if clarification:
            return ExternalActionSelectionDiagnosticsService.annotate(
                clarification,
                match_source="semanticFallback",
                ranked=ranked,
                reason_key="scoreGapClarification",
            )

        if action is None:
            return None

        if action.get("selectionScore") is None:
            return None

        try:
            top_score = float(action["selectionScore"])
        except (TypeError, ValueError):
            return None

        if top_score <= 0:
            return None

        # Sem overlap lexical: só executa com score semântico alto (JSON).
        if not action.get("selectionLexicalMatched"):
            pure_execute = ExternalActionScoreGapClarificationService._score_gap_float(
                "minTopScorePureSemanticExecute",
                0.55,
            )
            if top_score < pure_execute:
                return None

        parameters = {}

        if build_date_branch_parameters:
            parameters = build_date_branch_parameters(
                action,
                message,
                previous_messages=previous_messages,
            )

        parameters = ExternalActionProductRouteCatalogService.filter_parameters_to_schema(
            action,
            parameters,
        )

        arguments: dict = {
            "actionId": action["actionId"],
            "body": {
                "message": message,
            },
        }

        if parameters:
            arguments["parameters"] = parameters

        reason_key = read_policy_reason or "genericSemanticFallback"
        return ExternalActionSelectionDiagnosticsService.annotate(
            {
                "name": "execute_external_action",
                "arguments": arguments,
                "reason": (
                    ExternalActionResponseContentService.get(
                        "selectionReasons",
                        reason_key,
                    )
                    if read_policy_reason
                    else (
                        action.get("selectionReason")
                        or ExternalActionResponseContentService.get(
                            "selectionReasons",
                            "genericSemanticFallback",
                        )
                    )
                ),
            },
            match_source="semanticFallback",
            ranked=ranked,
            reason_key=reason_key,
        )
