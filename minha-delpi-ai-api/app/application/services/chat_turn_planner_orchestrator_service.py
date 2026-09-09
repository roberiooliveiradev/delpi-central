"""Orchestrator determinístico do bounded planner loop (≤2 rounds)."""

from __future__ import annotations

from typing import Any

from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.domain.models.action_descriptor import ActionCandidate
from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.chat_agentic_action_schema_service import (
    ChatAgenticActionSchemaService,
)
from app.domain.services.chat_candidate_set_service import ChatCandidateSetService
from app.domain.services.chat_goal_coverage_service import ChatGoalCoverageService
from app.domain.services.chat_planner_conversation_context_service import (
    ChatPlannerConversationContextService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)


class ChatTurnPlannerOrchestratorService:
    def __init__(
        self,
        *,
        retriever: RetrieveActionCandidatesService,
        planner: PlanExternalActionsService,
    ) -> None:
        self.retriever = retriever
        self.planner = planner

    def build_plan(
        self,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
        catalog_actions: list[dict[str, Any]] | None = None,
        previous_messages: list | None = None,
        workspace_context: dict[str, Any] | None = None,
        execution_context: dict[str, Any] | None = None,
    ) -> tuple[ActionPlan, dict[str, dict[str, Any]], dict[str, Any]]:
        max_rounds = OpenApiToolRoutingContentService.int_setting(
            "boundedLoop",
            "maxPlannerRoundsPerTurn",
            default=2,
        )
        max_action_searches = OpenApiToolRoutingContentService.int_setting(
            "boundedLoop",
            "maxActionSearchesPerTurn",
            default=2,
        )
        max_knowledge_searches = OpenApiToolRoutingContentService.int_setting(
            "boundedLoop",
            "maxKnowledgeSearchesPerTurn",
            default=2,
        )

        conversation_context = ChatPlannerConversationContextService.build(
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            execution_context=execution_context,
        )
        queries_used: list[str] = []
        candidates: list[ActionCandidate] = []
        action_search_count = 0
        knowledge_hits: list[dict[str, Any]] = []
        knowledge_search_count = 0
        round_count = 1

        from app.application.services.decompose_external_action_requests_service import (
            DecomposeExternalActionRequestsService,
        )

        subtasks = DecomposeExternalActionRequestsService.decompose(message)
        retrieve_queries = [item.text for item in subtasks] if len(subtasks) > 1 else [message]
        for query in retrieve_queries:
            text = str(query or "").strip()
            if not text:
                continue
            if action_search_count >= max_action_searches:
                break
            if text.lower() in {item.lower() for item in queries_used}:
                continue
            queries_used.append(text)
            action_search_count += 1
            self._merge_candidates(
                candidates,
                self.retriever.retrieve(
                    text,
                    allowed_action_ids=allowed_action_ids,
                    catalog_actions=catalog_actions,
                ),
            )
        if not queries_used:
            queries_used = [message]
            action_search_count = 1
            candidates = self.retriever.retrieve(
                message,
                allowed_action_ids=allowed_action_ids,
                catalog_actions=catalog_actions,
            )

        candidate_set_id = ChatCandidateSetService.build_id(
            candidates,
            queries=queries_used,
            allowed_action_ids=allowed_action_ids,
        )
        deterministic_compound = (
            len(subtasks) > 1 and getattr(self.planner, "llm_planner", None) is None
        )
        if deterministic_compound:
            plan = self._plan_subtask_coverage(
                subtasks,
                candidates,
                previous_messages=previous_messages,
                execution_context=execution_context,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
            )
        else:
            plan = self.planner.plan(
                message,
                candidates,
                previous_messages=previous_messages,
                execution_context=execution_context,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
            )
        plan = ActionPlan.from_dict(
            {
                **plan.as_dict(),
                "candidateSetId": candidate_set_id,
                "planVersion": plan.plan_version or "2",
            }
        )

        if (
            plan.wants_search_round
            and round_count < max_rounds
            and (plan.search_action_requests or plan.search_knowledge_requests)
        ):
            extra_queries = [
                item.query
                for item in plan.search_action_requests
                if item.query.strip() and item.query.strip().lower() != message.strip().lower()
            ]
            remaining = max(0, max_action_searches - action_search_count)
            for query in extra_queries[:remaining]:
                if query.strip().lower() in {q.strip().lower() for q in queries_used}:
                    continue
                queries_used.append(query)
                action_search_count += 1
                self._merge_candidates(
                    candidates,
                    self.retriever.retrieve(
                        query,
                        allowed_action_ids=allowed_action_ids,
                        catalog_actions=catalog_actions,
                    ),
                )

            knowledge_queries = [item.query for item in plan.search_knowledge_requests if item.query.strip()]
            knowledge_hits, knowledge_search_count = self._search_knowledge(
                knowledge_queries[:max_knowledge_searches],
                workspace_context=workspace_context,
            )
            if knowledge_hits:
                conversation_context = (
                    conversation_context.rstrip()
                    + "\nKnowledge excerpts (untrusted):\n"
                    + str(knowledge_hits[:6])
                )

            candidate_set_id = ChatCandidateSetService.build_id(
                candidates,
                queries=queries_used,
                allowed_action_ids=allowed_action_ids,
            )
            round_count += 1
            plan = self.planner.plan(
                message,
                candidates,
                previous_messages=previous_messages,
                execution_context=execution_context,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
            )
            plan = ActionPlan.from_dict(
                {
                    **plan.as_dict(),
                    "candidateSetId": candidate_set_id,
                    "planVersion": plan.plan_version or "2",
                }
            )

        if (
            len(subtasks) > 1
            and not plan.wants_search_round
            and len(plan.steps) < len(subtasks)
            and getattr(self.planner, "llm_planner", None) is not None
        ):
            filled = self._plan_subtask_coverage(
                subtasks,
                candidates,
                previous_messages=previous_messages,
                execution_context=execution_context,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
            )
            plan = self._union_plans(plan, filled)

        plan = self._with_subtask_goals(plan, subtasks)
        plan = self._with_requested_presentation(plan, message)
        coverage = ChatGoalCoverageService.evaluate(plan)
        actions_by_id: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            if candidate.action_id:
                actions_by_id[candidate.action_id] = candidate.raw_action
        for action in catalog_actions or []:
            action_id = str(action.get("actionId") or "").strip()
            if action_id and action_id not in actions_by_id:
                actions_by_id[action_id] = dict(action)

        trace = {
            "plannerRoundCount": round_count,
            "actionSearchCount": action_search_count,
            "knowledgeSearchCount": knowledge_search_count,
            "candidateSetId": candidate_set_id,
            "candidateCount": len(candidates),
            "candidateSummaries": ChatCandidateSetService.slim_summaries(candidates),
            "goalCoverage": coverage.as_dict(),
            "retrievalQueries": queries_used,
            "maxPlannerRoundsPerTurn": max_rounds,
        }
        metadata = dict(plan.metadata or {})
        metadata["boundedPlanner"] = trace
        plan = ActionPlan.from_dict({**plan.as_dict(), "metadata": metadata})
        return plan, actions_by_id, trace

    @classmethod
    def _merge_candidates(
        cls,
        candidates: list[ActionCandidate],
        incoming: list[ActionCandidate],
    ) -> None:
        for candidate in incoming:
            existing = next(
                (item for item in candidates if item.action_id == candidate.action_id),
                None,
            )
            if existing is None:
                candidates.append(candidate)
            elif float(candidate.score or 0.0) > float(existing.score or 0.0):
                candidates[candidates.index(existing)] = candidate

    @classmethod
    def _search_knowledge(
        cls,
        queries: list[str],
        *,
        workspace_context: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], int]:
        if not queries:
            return [], 0
        try:
            from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
            from app.composition.knowledge_composer import make_search_knowledge_use_case
        except Exception:
            return [], 0

        filters: dict[str, Any] | None = None
        if isinstance(workspace_context, dict):
            agent = workspace_context.get("agent") if isinstance(workspace_context.get("agent"), dict) else {}
            project = workspace_context.get("project") if isinstance(workspace_context.get("project"), dict) else {}
            filters = {}
            if agent.get("id"):
                filters["agentId"] = agent.get("id")
            if project.get("id"):
                filters["projectId"] = project.get("id")
            if not filters:
                filters = None

        hits: list[dict[str, Any]] = []
        count = 0
        try:
            use_case = make_search_knowledge_use_case()
        except Exception:
            return [], 0
        for query in queries:
            count += 1
            try:
                rows = use_case.execute(
                    SearchKnowledgeRequest(query=query, limit=4, filters=filters)
                )
            except Exception:
                continue
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                hits.append(
                    {
                        "chunkId": row.get("id") or row.get("chunkId"),
                        "source": row.get("source") or row.get("documentId"),
                        "score": row.get("score"),
                        "excerpt": str(row.get("content") or row.get("text") or "")[:280],
                    }
                )
        return hits, count

    def _plan_subtask_coverage(
        self,
        subtasks: list,
        candidates: list[ActionCandidate],
        *,
        previous_messages: list | None,
        execution_context: dict[str, Any] | None,
        conversation_context: str,
        candidate_set_id: str,
    ) -> ActionPlan:
        from app.application.services.openapi_first_selection_bridge_service import (
            OpenApiFirstSelectionBridgeService,
        )

        steps: list[ActionPlanStep] = []
        seen: set[str] = set()
        rolling = dict(execution_context or {})
        allowed = [item.action_id for item in candidates if item.action_id]
        catalog = [item.raw_action for item in candidates]
        for index, subtask in enumerate(subtasks):
            text = str(getattr(subtask, "text", "") or "").strip()
            if not text:
                continue
            fragment_candidates = self.retriever.retrieve(
                text,
                allowed_action_ids=allowed,
                catalog_actions=catalog,
            ) or list(candidates)
            bind_context = dict(rolling)
            bind_context.pop("actionId", None)
            fragment = self.planner.plan(
                text,
                fragment_candidates,
                previous_messages=previous_messages,
                execution_context=bind_context,
                max_steps=1,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
            )
            for step in fragment.steps:
                if not step.action_id or step.action_id in seen:
                    continue
                seen.add(step.action_id)
                payload = step.as_dict()
                payload["goalIds"] = [f"g{index + 1}"]
                payload["stepId"] = payload.get("stepId") or f"s{index + 1}"
                bound = ActionPlanStep.from_dict(payload)
                steps.append(bound)
                rolling = OpenApiFirstSelectionBridgeService.merge_execution_context(
                    rolling,
                    provider_key=None,
                    action_id=step.action_id,
                    arguments=step.arguments,
                )
        goals = [
            ActionPlanGoal(goal_id=f"g{index + 1}", intent=str(item.text or "")[:160])
            for index, item in enumerate(subtasks)
            if str(getattr(item, "text", "") or "").strip()
        ]
        return ActionPlan.from_dict(
            {
                "steps": [step.as_dict() for step in steps],
                "goals": [goal.as_dict() for goal in goals],
                "mode": "EXECUTE" if steps else "CLARIFY",
                "selectionMode": "openapi_first",
                "planVersion": "2",
                "candidateSetId": candidate_set_id,
                "metadata": {"compound": True, "subtaskCount": len(subtasks)},
            }
        )

    @classmethod
    def _union_plans(cls, primary: ActionPlan, secondary: ActionPlan) -> ActionPlan:
        seen = {step.action_id for step in primary.steps if step.action_id}
        extra = [step for step in secondary.steps if step.action_id not in seen]
        if not extra:
            return primary
        payload = primary.as_dict()
        payload["steps"] = [step.as_dict() for step in primary.steps] + [
            step.as_dict() for step in extra
        ]
        if secondary.goals and not primary.goals:
            payload["goals"] = [goal.as_dict() for goal in secondary.goals]
        metadata = dict(primary.metadata or {})
        metadata["compoundCoverageFill"] = [step.action_id for step in extra]
        payload["metadata"] = metadata
        payload["mode"] = "EXECUTE"
        return ActionPlan.from_dict(payload)

    @classmethod
    def _with_subtask_goals(cls, plan: ActionPlan, subtasks: list) -> ActionPlan:
        if len(subtasks) <= 1:
            return plan
        payload = plan.as_dict()
        if not plan.goals:
            payload["goals"] = [
                ActionPlanGoal(
                    goal_id=f"g{index + 1}",
                    intent=str(getattr(item, "text", "") or "")[:160],
                ).as_dict()
                for index, item in enumerate(subtasks)
            ]
        steps = []
        for index, step in enumerate(plan.steps):
            item = step.as_dict()
            if not item.get("goalIds"):
                item["goalIds"] = [f"g{min(index, max(len(subtasks) - 1, 0)) + 1}"]
            if not item.get("stepId"):
                item["stepId"] = f"s{index + 1}"
            steps.append(item)
        payload["steps"] = steps
        return ActionPlan.from_dict(payload)

    @classmethod
    def _with_requested_presentation(cls, plan: ActionPlan, message: str) -> ActionPlan:
        if plan.requested_presentation:
            return plan
        preferred = ChatPresentationUserFormatPreferenceService.normalize_from_message(
            None,
            message,
        )
        if not preferred:
            return plan
        payload = plan.as_dict()
        payload["requestedPresentation"] = preferred
        return ActionPlan.from_dict(payload)

    @classmethod
    def slim_catalog(cls, candidates: list[ActionCandidate]) -> list[dict[str, Any]]:
        catalog = [
            ChatAgenticActionSchemaService.build_slim_action(
                item.raw_action,
                prefer_openapi_examples=True,
            )
            for item in candidates
        ]
        return [entry for entry in catalog if entry]
