"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService
from app.domain.services.chat_sql_dialect_resolver_service import ChatSqlDialectResolverService
from app.domain.services.chat_sql_memory_workspace_service import ChatSqlMemoryWorkspaceService
from app.domain.services.chat_sql_performance_advisor_service import ChatSqlPerformanceAdvisorService
from app.domain.services.chat_sql_query_refinement_service import ChatSqlQueryRefinementService
from app.domain.services.chat_sql_review_service import ChatSqlReviewService
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_activation_service import (
    ChatAdvancedSqlSpecialistActivationService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistPipelineService:
    @classmethod
    def build_pipeline_snapshot(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> dict[str, Any] | None:
        if not sql_specialist_service().should_activate(message, workspace_context=workspace_context):
            return None

        mode = sql_specialist_service().classify_mode(message, previous_messages=previous_messages)
        dialect = ChatSqlDialectResolverService.resolve(message, workspace_context=workspace_context)
        workspace = ChatSqlMemoryWorkspaceService.build_workspace(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )
        sql_text = workspace.get("currentSql") or ChatSqlPerformanceAdvisorService.extract_sql_block(
            message
        )
        blocked = ChatSqlSafetyService.contains_destructive_sql(message) or (
            bool(sql_text) and ChatSqlSafetyService.contains_destructive_sql(str(sql_text))
        )
        performance = (
            ChatSqlPerformanceAdvisorService.analyze(str(sql_text), dialect=str(dialect["dialect"]))
            if sql_text
            else ChatSqlPerformanceAdvisorService.analyze_message(
                message,
                dialect=str(dialect["dialect"]),
            )
        )

        from app.domain.services.chat_sql_schema_discovery_service import (
            ChatSqlSchemaDiscoveryService,
        )

        schema_discovery = ChatSqlSchemaDiscoveryService.build_schema_snapshot(
            message=message,
            tool_calls=tool_calls,
            current_sql=sql_text,
        )
        review = (
            ChatSqlReviewService.review(str(sql_text), dialect=str(dialect["dialect"]))
            if sql_text and mode in {"review", "optimize", "execute"}
            else None
        )

        from app.domain.services.chat_sql_result_analyzer_service import (
            ChatSqlResultAnalyzerService,
        )
        from app.domain.services.chat_sql_visualization_advisor_service import (
            ChatSqlVisualizationAdvisorService,
        )
        from app.domain.services.chat_sql_optimization_advisor_service import (
            ChatSqlOptimizationAdvisorService,
        )
        from app.domain.services.chat_sql_query_pattern_advisor_service import (
            ChatSqlQueryPatternAdvisorService,
        )

        result_analysis = ChatSqlResultAnalyzerService.analyze_tool_calls(tool_calls)
        visualization = ChatSqlVisualizationAdvisorService.recommend(
            message=message,
            mode=mode,
            result_analysis=result_analysis,
        )
        pattern_advice = ChatSqlQueryPatternAdvisorService.recommend(message)
        optimization = None

        if sql_text and mode in {"optimize", "review", "execute", "create"}:
            optimization = ChatSqlOptimizationAdvisorService.advise(
                str(sql_text),
                dialect=str(dialect["dialect"]),
                mode=mode,
            )

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        agent_actions = ChatSqlAuthoringGuidanceService.agent_actions_available(workspace_context)

        return {
            "mode": mode,
            "dialect": dialect,
            "workspace": workspace,
            "agentActionsAvailable": agent_actions,
            "plannerHints": sql_specialist_service().build_planner_hints(message) + list(pattern_advice.get("hints") or []),
            "patternAdvice": pattern_advice,
            "performance": performance,
            "optimization": optimization,
            "review": review,
            "blocked": blocked,
            "resultAnalysis": result_analysis,
            "visualizationAdvice": visualization,
            "schemaDiscovery": schema_discovery,
            "schemaPrefetchRecommended": sql_specialist_service().should_prefetch_schema(
                message=message,
                mode=mode,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
            ),
        }

    @classmethod
    def build_planner_hints(cls, message: str | None) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return []

        hints: list[str] = []

        for patterns, hint in ChatSqlIntentVocabularyService.planner_hints():
            if any(pattern in normalized for pattern in patterns):
                hints.append(hint)

        if re.search(r"\bjoin\b", normalized):
            hints.append("check_join_granularity")

        return hints

    @classmethod
    def should_prefetch_schema(
        cls,
        *,
        message: str | None,
        mode: SqlSpecialistMode | None = None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if not ChatAdvancedSqlSpecialistActivationService._sql_authoring_enabled(workspace_context):
            return False

        resolved_mode = mode or sql_specialist_service().classify_mode(message, previous_messages=previous_messages)

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        if not ChatSqlAuthoringGuidanceService.agent_actions_available(workspace_context):
            return False

        if resolved_mode == "schema_explore":
            return True

        if resolved_mode == "review" and ChatSqlPerformanceAdvisorService.extract_sql_block(
            str(message or "")
        ):
            return True

        if resolved_mode in {"create", "incremental_edit"}:
            return ChatSqlAuthoringGuidanceService.is_custom_sql_authoring(
                str(message or "")
            )

        return ChatSqlAuthoringGuidanceService.should_prefetch_schema(
            message=str(message or ""),
            workspace_context=workspace_context,
            previous_messages=previous_messages,
        )

    @classmethod
    def requires_llm_response(cls, snapshot: dict[str, Any] | None) -> bool:
        if not snapshot:
            return False

        mode = str(snapshot.get("mode") or "none")

        if mode in {"create", "review", "explain", "optimize", "incremental_edit"}:
            return True

        if mode == "schema_explore":
            normalized = ChatMessageNormalizationService.normalize_for_matching(
                str(snapshot.get("message") or "")
            )

            return any(
                term in normalized
                for term in ("relacion", "join", "ligar", "associar", "chave", "fk ")
            )

        return False

