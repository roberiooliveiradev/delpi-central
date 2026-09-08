"""Ponte OpenAPI-first: retrieve → plan → validate → tool calls do chat."""

from __future__ import annotations

from typing import Any

from app.application.services.external_actions.external_action_selection_diagnostics_service import (
    ExternalActionSelectionDiagnosticsService,
)
from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.application.services.validate_action_arguments_service import (
    ValidateActionArgumentsService,
)
from app.domain.models.action_plan import ActionPlan
from app.domain.services.chat_write_confirmation_service import ChatWriteConfirmationService
from app.domain.services.openapi_planner_mode_service import (
    OpenApiPlannerModeDecision,
    OpenApiPlannerModeService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)


class OpenApiFirstSelectionBridgeService:
    def __init__(
        self,
        repository=None,
        *,
        semantic_ranker=None,
        planner: PlanExternalActionsService | None = None,
        validator: ValidateActionArgumentsService | None = None,
    ) -> None:
        self.repository = repository
        self.retriever = RetrieveActionCandidatesService(
            repository,
            semantic_ranker=semantic_ranker,
        )
        self.planner = planner or PlanExternalActionsService()
        self.validator = validator or ValidateActionArgumentsService()

    def plan_tool_calls(
        self,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
        catalog_actions: list[dict[str, Any]] | None = None,
        previous_messages: list | None = None,
        workspace_context: dict | None = None,
        mode_decision: OpenApiPlannerModeDecision | None = None,
    ) -> list[dict[str, Any]]:
        decision = mode_decision or OpenApiPlannerModeService.decide(
            provider_keys=self._provider_keys(catalog_actions, allowed_action_ids),
            agent_id=self._agent_id(workspace_context),
        )
        if not decision.use_openapi_selection and not decision.run_shadow_compare:
            return []

        execution_context = self._execution_context(workspace_context)
        candidates = self.retriever.retrieve(
            message,
            allowed_action_ids=allowed_action_ids,
            catalog_actions=catalog_actions,
        )
        plan = self.planner.plan(
            message,
            candidates,
            previous_messages=previous_messages,
            execution_context=execution_context,
        )
        actions_by_id: dict[str, dict[str, Any]] = {}
        for action in catalog_actions or []:
            action_id = str(action.get("actionId") or "").strip()
            if action_id:
                actions_by_id[action_id] = dict(action)
        for candidate in candidates:
            actions_by_id[candidate.action_id] = candidate.raw_action

        planned = self._plan_to_tool_calls(
            plan,
            message=message,
            actions_by_id=actions_by_id,
        )
        annotated: list[dict[str, Any]] = []
        for item in planned:
            meta = dict(item.get("metadata") or {})
            meta["selectionMode"] = "openapi_first"
            meta["openapiPlannerMode"] = decision.mode
            item["metadata"] = meta
            enriched = ExternalActionSelectionDiagnosticsService.annotate(
                item,
                match_source="openapiFirst",
                reason_key="openapiFirstPlan",
            )
            annotated.append(enriched if isinstance(enriched, dict) else item)
        return annotated

    @classmethod
    def compare_shadow(
        cls,
        *,
        legacy_planned: list[dict[str, Any]],
        openapi_planned: list[dict[str, Any]],
    ) -> dict[str, Any]:
        legacy_ids = [
            str((item.get("arguments") or {}).get("actionId") or item.get("actionId") or "")
            for item in legacy_planned
        ]
        openapi_ids = [
            str((item.get("arguments") or {}).get("actionId") or item.get("actionId") or "")
            for item in openapi_planned
        ]
        diverged = legacy_ids != openapi_ids
        return {
            "selectionMode": "shadow",
            "legacyActionIds": legacy_ids,
            "openapiActionIds": openapi_ids,
            "diverged": diverged,
            "reason": OpenApiToolRoutingContentService.get(
                "selectionReasons",
                "openapiFirstShadowDivergence",
            )
            if diverged
            else None,
        }

    def _plan_to_tool_calls(
        self,
        plan: ActionPlan,
        *,
        message: str,
        actions_by_id: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if plan.clarify:
            return [
                {
                    "name": "clarify_external_action",
                    "arguments": {"message": plan.clarify},
                    "reason": plan.clarify,
                    "directAnswer": plan.clarify,
                    "metadata": {
                        "selectionMode": "openapi_first",
                        **(plan.metadata or {}),
                    },
                }
            ]

        results: list[dict[str, Any]] = []
        for step in plan.steps:
            action = dict(actions_by_id.get(step.action_id) or {"actionId": step.action_id})
            if ChatWriteConfirmationService.action_requires_confirmation(
                action
            ) and not ChatWriteConfirmationService.user_confirmed(message):
                confirm_msg = OpenApiToolRoutingContentService.get(
                    "selectionReasons",
                    "openapiFirstWriteNeedsConfirm",
                )
                return [
                    {
                        "name": "clarify_external_action",
                        "arguments": {"message": confirm_msg},
                        "reason": confirm_msg,
                        "directAnswer": confirm_msg,
                        "metadata": {
                            "selectionMode": "openapi_first",
                            "requiresConfirmation": True,
                            "pendingActionId": step.action_id,
                        },
                    }
                ]

            normalized, error = self.validator.try_validate(
                provider={"enabled": True},
                action=action,
                arguments=step.arguments,
            )
            if error is not None:
                clarify = str(error)
                return [
                    {
                        "name": "clarify_external_action",
                        "arguments": {"message": clarify},
                        "reason": clarify,
                        "directAnswer": clarify,
                        "metadata": {
                            "selectionMode": "openapi_first",
                            "validationError": error.to_metadata(),
                        },
                    }
                ]

            payload = {
                "name": "execute_external_action",
                "arguments": normalized or step.arguments,
                "reason": step.reason
                or OpenApiToolRoutingContentService.get(
                    "selectionReasons",
                    "openapiFirstPlan",
                ),
                "metadata": {
                    "selectionMode": "openapi_first",
                    "providerKey": action.get("providerKey"),
                    "operationId": action.get("operationId"),
                    "requiresConfirmation": ChatWriteConfirmationService.action_requires_confirmation(
                        action
                    ),
                },
            }
            results.append(payload)
        return results

    @classmethod
    def _execution_context(cls, workspace_context: dict | None) -> dict[str, Any]:
        if not isinstance(workspace_context, dict):
            return {}
        working = workspace_context.get("workingMemory")
        if not isinstance(working, dict):
            return {}
        ctx = working.get("executionContext")
        return dict(ctx) if isinstance(ctx, dict) else {}

    @classmethod
    def _agent_id(cls, workspace_context: dict | None) -> str | None:
        if not isinstance(workspace_context, dict):
            return None
        for key in ("agentId", "activeAgentId", "contextAgentId"):
            value = workspace_context.get(key)
            if value:
                return str(value).strip()
        agent = workspace_context.get("agent")
        if isinstance(agent, dict) and agent.get("id"):
            return str(agent["id"]).strip()
        return None

    def _provider_keys(
        self,
        catalog_actions: list[dict[str, Any]] | None,
        allowed_action_ids: list[str] | None,
    ) -> set[str]:
        keys: set[str] = set()
        for action in catalog_actions or []:
            key = str(action.get("providerKey") or "").strip()
            if key:
                keys.add(key)
        if keys:
            return keys
        # Infer from actionId prefix (provider_key.operation)
        for action_id in allowed_action_ids or []:
            text = str(action_id)
            if "." in text:
                keys.add(text.split(".", 1)[0])
        return keys

    @classmethod
    def merge_execution_context(
        cls,
        previous: dict[str, Any] | None,
        *,
        provider_key: str | None,
        action_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        base = dict(previous or {})
        parameters = {}
        if isinstance(arguments.get("parameters"), dict):
            parameters = dict(arguments["parameters"])
        base.update(
            {
                "providerKey": provider_key,
                "actionId": action_id,
                "parameters": parameters,
            }
        )
        if "body" in arguments:
            base["body"] = arguments.get("body")
        return base
