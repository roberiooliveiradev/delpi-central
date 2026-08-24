"""Delegate de turn prep — análise estruturada pós-heurística, pré-tools."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_turn_analysis_service import (
    ChatTurnAnalysisResult,
    ChatTurnAnalysisService,
)
from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.turn-analysis-prep")

_turn_analysis_ran: ContextVar[bool] = ContextVar("turn_analysis_ran", default=False)


@dataclass(frozen=True)
class ChatTurnPreparationTurnAnalysisOutcome:
    result: ChatTurnAnalysisResult | None
    direct_answer: str | None
    skip_tools: bool


class ChatTurnPreparationTurnAnalysisService:
    @classmethod
    def ran_this_turn(cls) -> bool:
        return bool(_turn_analysis_ran.get())

    @classmethod
    def mark_ran(cls, value: bool = True) -> None:
        _turn_analysis_ran.set(bool(value))

    @classmethod
    def reset_ran(cls) -> None:
        _turn_analysis_ran.set(False)

    @classmethod
    def maybe_analyze(
        cls,
        *,
        message: str,
        request,
        workspace_context: dict,
        history_source: list[Any],
        pipeline_stages: list[str],
        has_direct_answer: bool,
        llm_gateway=None,
        external_action_repository=None,
        allow_compose_gateway: bool = True,
        tools_already_skipped: bool = False,
    ) -> ChatTurnPreparationTurnAnalysisOutcome:
        cls.reset_ran()

        if has_direct_answer:
            return ChatTurnPreparationTurnAnalysisOutcome(
                result=None,
                direct_answer=None,
                skip_tools=False,
            )

        response_mode = ChatResponseModeService.normalize(
            getattr(request, "response_mode", None)
        )
        allowed_action_ids = [
            str(item).strip()
            for item in (workspace_context.get("allowedActionIds") or [])
            if str(item).strip()
        ]

        route = ChatIntentRouterService.classify(
            message,
            previous_messages=history_source,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
            attachment_ids=list(getattr(request, "attachment_ids", None) or []),
        )

        enabled = bool(getattr(Settings, "CHAT_TURN_ANALYSIS_ENABLED", True))
        try:
            from app.application.services.chat_intelligence_runtime_access import (
                resolve_chat_intelligence_runtime,
            )

            runtime = resolve_chat_intelligence_runtime()
            if hasattr(runtime, "turn_analysis_enabled"):
                enabled = bool(runtime.turn_analysis_enabled)
        except Exception:
            pass

        if not ChatTurnAnalysisService.should_analyze(
            response_mode=response_mode,
            heuristic_intent=route.intent,
            heuristic_decision=route.decision,
            heuristic_reason=route.reason,
            heuristic_confidence=route.confidence,
            pipeline_stages=pipeline_stages,
            has_direct_answer=False,
            turn_analysis_enabled=enabled,
            tools_already_skipped=tools_already_skipped,
        ):
            return ChatTurnPreparationTurnAnalysisOutcome(
                result=None,
                direct_answer=None,
                skip_tools=False,
            )

        if llm_gateway is None:
            if not allow_compose_gateway:
                return ChatTurnPreparationTurnAnalysisOutcome(
                    result=None,
                    direct_answer=None,
                    skip_tools=False,
                )
            from app.composition.llm_composer import make_llm_gateway

            llm_gateway = make_llm_gateway()

        if external_action_repository is None:
            try:
                from app.composition.repository_composer import (
                    make_external_action_repository,
                )

                external_action_repository = make_external_action_repository()
            except Exception:
                external_action_repository = None

        agent = workspace_context.get("agent")
        agent_metadata = None
        if isinstance(agent, dict):
            agent_metadata = agent.get("metadata")
        elif workspace_context.get("agentMetadata"):
            agent_metadata = workspace_context.get("agentMetadata")

        skills_bindings = ChatSkillRegistry.list_agent_bindings(
            agent_metadata=agent_metadata if isinstance(agent_metadata, dict) else None,
            allowed_action_ids=allowed_action_ids,
            has_agent=bool(agent),
        )
        enabled_skills = [
            item for item in skills_bindings if isinstance(item, dict) and item.get("enabled")
        ]
        skill_keys = {
            str(item.get("skillKey") or "").strip().lower()
            for item in enabled_skills
            if str(item.get("skillKey") or "").strip()
        }
        skills_lines = [
            f"- {item.get('skillKey')}: {item.get('label') or item.get('description') or ''}"
            for item in enabled_skills[:12]
        ]

        action_lines: list[str] = []
        allowed_set = set(allowed_action_ids)
        if external_action_repository and allowed_action_ids:
            try:
                candidates = external_action_repository.find_candidate_actions(
                    message,
                    limit=int(getattr(Settings, "CHAT_AGENTIC_CATALOG_MAX_ACTIONS", 12) or 12),
                    allowed_action_ids=allowed_action_ids,
                )
            except Exception:
                logger.exception("turn_analysis_catalog_failed")
                candidates = []

            for action in candidates or []:
                if not isinstance(action, dict):
                    continue
                action_id = str(action.get("actionId") or "").strip()
                if not action_id:
                    continue
                allowed_set.add(action_id)
                action_lines.append(
                    "{actionId} | {method} {path} | {summary}".format(
                        actionId=action_id,
                        method=action.get("method") or "",
                        path=action.get("path") or "",
                        summary=action.get("summary") or action.get("description") or "",
                    )[:220]
                )

        cls.mark_ran(True)
        turn_grounding = workspace_context.get("turnGrounding") or {}
        grounding_status = (
            str(turn_grounding.get("status") or "").strip()
            if isinstance(turn_grounding, dict)
            else ""
        )
        working_memory = workspace_context.get("workingMemory") or {}
        last_result_excerpt = (
            working_memory.get("lastResultExcerpt")
            if isinstance(working_memory, dict)
            else None
        )
        if not isinstance(last_result_excerpt, dict):
            excerpt_block = turn_grounding.get("excerpt") if isinstance(turn_grounding, dict) else None
            last_result_excerpt = excerpt_block if isinstance(excerpt_block, dict) else None

        turn_grounding_stage = (
            str(turn_grounding.get("stage") or "").strip()
            if isinstance(turn_grounding, dict)
            else ""
        )

        result = ChatTurnAnalysisService.analyze(
            llm_gateway=llm_gateway,
            message=message,
            response_mode=response_mode,
            heuristic_intent=str(route.intent or ""),
            heuristic_confidence=float(route.confidence or 0),
            heuristic_reason=str(route.reason or ""),
            skills_catalog_lines=skills_lines,
            actions_catalog_lines=action_lines,
            allowed_action_ids=allowed_set,
            allowed_skill_keys=skill_keys,
            grounding_status=grounding_status or None,
            last_result_excerpt=last_result_excerpt,
            turn_grounding_stage=turn_grounding_stage or None,
        )

        direct = result.direct_answer() if result.decision == "clarify" else None
        skip_tools = result.decision == "clarify"

        return ChatTurnPreparationTurnAnalysisOutcome(
            result=result,
            direct_answer=direct,
            skip_tools=skip_tools,
        )
