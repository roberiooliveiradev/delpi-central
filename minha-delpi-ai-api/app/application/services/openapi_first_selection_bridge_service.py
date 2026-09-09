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
        self._planner_override = planner
        self._planner: PlanExternalActionsService | None = planner
        self.validator = validator or ValidateActionArgumentsService()

    @property
    def planner(self) -> PlanExternalActionsService:
        if self._planner is not None:
            return self._planner
        llm_adapter = None
        try:
            from app.application.services.openapi_llm_action_planner_service import (
                OpenApiLlmActionPlannerService,
            )

            llm_adapter = OpenApiLlmActionPlannerService.from_stack()
        except Exception:
            llm_adapter = None
        self._planner = PlanExternalActionsService(
            # Always-on: same prose/chat gateway. Fail-soft inside the adapter.
            llm_planner=llm_adapter if llm_adapter is not None else None,
        )
        return self._planner

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
        del mode_decision
        execution_context = self._execution_context(
            workspace_context,
            previous_messages=previous_messages,
        )
        actions_by_id: dict[str, dict[str, Any]] = {}
        for action in catalog_actions or []:
            action_id = str(action.get("actionId") or "").strip()
            if action_id:
                actions_by_id[action_id] = dict(action)

        rolling_context = dict(execution_context or {})
        from app.application.services.chat_turn_planner_orchestrator_service import (
            ChatTurnPlannerOrchestratorService,
        )

        orchestrator = ChatTurnPlannerOrchestratorService(
            retriever=self.retriever,
            planner=self.planner,
        )
        plan, actions_by_id, trace = orchestrator.build_plan(
            message,
            allowed_action_ids=allowed_action_ids,
            catalog_actions=catalog_actions,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            execution_context=rolling_context,
        )
        for step in plan.steps:
            resolved = self._resolve_action_dict(
                step.action_id,
                actions_by_id=actions_by_id,
                allowed_action_ids=allowed_action_ids,
                catalog_actions=catalog_actions,
                message=message,
            )
            if resolved:
                actions_by_id[step.action_id] = resolved
        candidate_action_ids = [
            str(item.get("actionId") or "").strip()
            for item in (trace.get("candidateSummaries") or [])
            if isinstance(item, dict) and str(item.get("actionId") or "").strip()
        ]
        if not candidate_action_ids:
            candidate_action_ids = [
                step.action_id for step in plan.steps if step.action_id
            ]
        planned = self._plan_to_tool_calls(
            plan,
            message=message,
            actions_by_id=actions_by_id,
            allowed_action_ids=allowed_action_ids,
            candidate_action_ids=candidate_action_ids,
            candidate_set_id=str(trace.get("candidateSetId") or plan.candidate_set_id or ""),
        )
        annotated: list[dict[str, Any]] = []
        for item in planned:
            meta = dict(item.get("metadata") or {})
            meta["selectionMode"] = "openapi_first"
            meta["openapiPlannerMode"] = "on"
            meta["boundedPlannerMode"] = "on"
            meta.update(trace)
            item["metadata"] = meta
            enriched = ExternalActionSelectionDiagnosticsService.annotate(
                item,
                match_source="openapiFirst",
                reason_key="openapiFirstPlan",
            )
            annotated.append(enriched if isinstance(enriched, dict) else item)
        return annotated


    def _plan_to_tool_calls(
        self,
        plan: ActionPlan,
        *,
        message: str,
        actions_by_id: dict[str, dict[str, Any]],
        allowed_action_ids: list[str] | None = None,
        candidate_action_ids: list[str] | None = None,
        candidate_set_id: str = "",
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_candidate_set_service import ChatCandidateSetService

        if plan.clarify and not plan.steps:
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

        membership_ids = candidate_action_ids or list(actions_by_id.keys())
        results: list[dict[str, Any]] = []
        for step in plan.steps:
            if not ChatCandidateSetService.contains(
                step.action_id,
                candidate_action_ids=membership_ids,
                allowed_action_ids=allowed_action_ids,
            ):
                continue
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
                # Keep already-validated compound steps; skip only the bad sibling.
                if results:
                    continue
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

            args = dict(normalized or step.arguments or {})
            parameters = dict(args.get("parameters") or {})
            if plan.requested_presentation:
                from app.domain.services.chat_presentation_preference_contract_service import (
                    ChatPresentationPreferenceContractService,
                )

                session_token = ChatPresentationPreferenceContractService.as_session_response_format(
                    plan.requested_presentation
                )
                if session_token:
                    parameters.setdefault("sessionResponseFormat", session_token)
                    parameters.setdefault(
                        "requestedPresentation",
                        plan.requested_presentation,
                    )
                args["parameters"] = parameters
            args["candidateSetId"] = candidate_set_id or plan.candidate_set_id
            args["candidateActionIds"] = list(membership_ids)

            payload = {
                "name": "execute_external_action",
                "arguments": args,
                "reason": step.reason
                or OpenApiToolRoutingContentService.get(
                    "selectionReasons",
                    "openapiFirstPlan",
                ),
                "metadata": {
                    "selectionMode": "openapi_first",
                    "providerKey": action.get("providerKey"),
                    "operationId": action.get("operationId"),
                    "path": action.get("path"),
                    "method": action.get("method"),
                    "actionId": step.action_id,
                    "goalIds": list(step.goal_ids),
                    "stepId": step.step_id,
                    "requestedPresentation": plan.requested_presentation,
                    "candidateSetId": candidate_set_id or plan.candidate_set_id,
                    "candidateActionIds": list(membership_ids),
                    "executionContext": self.merge_execution_context(
                        None,
                        provider_key=str(action.get("providerKey") or "") or None,
                        action_id=step.action_id,
                        arguments=args,
                    ),
                    "confidence": step.confidence,
                    "requiresConfirmation": ChatWriteConfirmationService.action_requires_confirmation(
                        action
                    ),
                },
            }
            results.append(payload)
        return results

    def _resolve_action_dict(
        self,
        action_id: str,
        *,
        actions_by_id: dict[str, dict[str, Any]],
        allowed_action_ids: list[str] | None,
        catalog_actions: list[dict[str, Any]] | None,
        message: str,
    ) -> dict[str, Any] | None:
        """Ensure validate/execute see full OpenAPI parametersSchema for the step."""
        action_id = str(action_id or "").strip()
        if not action_id:
            return None

        current = actions_by_id.get(action_id)
        if isinstance(current, dict) and (
            current.get("parametersSchema")
            or current.get("parameters_schema")
            or current.get("path")
        ):
            return current

        for action in catalog_actions or []:
            if str(action.get("actionId") or "").strip() == action_id:
                return dict(action)

        repo = self.repository
        if repo is not None and hasattr(repo, "get_action_for_execution"):
            try:
                payload = repo.get_action_for_execution(action_id)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                nested = payload.get("action")
                if isinstance(nested, dict) and nested.get("actionId"):
                    return dict(nested)

        if repo is not None and hasattr(repo, "find_candidate_actions"):
            try:
                rows = repo.find_candidate_actions(
                    action_id,
                    limit=5,
                    allowed_action_ids=[action_id],
                )
            except Exception:
                rows = []
            for row in rows or []:
                if str(row.get("actionId") or "").strip() == action_id:
                    return dict(row)

        for candidate in self.retriever.retrieve(
            message,
            allowed_action_ids=allowed_action_ids,
            catalog_actions=catalog_actions,
        ):
            if candidate.action_id == action_id:
                return candidate.raw_action
        return current if isinstance(current, dict) else None

    @classmethod
    def _execution_context(
        cls,
        workspace_context: dict | None,
        *,
        previous_messages: list | None = None,
    ) -> dict[str, Any]:
        if isinstance(workspace_context, dict):
            working = workspace_context.get("workingMemory")
            if isinstance(working, dict):
                ctx = working.get("executionContext")
                if isinstance(ctx, dict) and ctx.get("actionId"):
                    return dict(ctx)

        from app.application.services.external_actions.external_action_selection_support_service import (
            ExternalActionSelectionSupportService,
        )

        previous = ExternalActionSelectionSupportService.resolve_last_external_action_state(
            previous_messages
        )
        return previous or {}

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
