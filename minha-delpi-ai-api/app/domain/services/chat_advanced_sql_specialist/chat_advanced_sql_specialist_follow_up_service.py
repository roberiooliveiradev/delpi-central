"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService

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



class ChatAdvancedSqlSpecialistFollowUpService:
    @classmethod
    def resolve_max_tool_calls(cls, message: str | None, agent_max: int | None) -> int:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        cap = 50
        base = max(1, min(int(agent_max or 5), cap))

        if sql_specialist_service().should_activate(message) or ChatSqlIntentService.is_sql_conversation_turn(message):
            return cap

        return base

    @classmethod
    def build_follow_up_suggestions(
        cls,
        *,
        message: str | None,
        snapshot: dict[str, Any] | None = None,
        tool_calls: list | None = None,
    ) -> list[dict[str, str]]:
        if snapshot is None:
            snapshot = sql_specialist_service().build_pipeline_snapshot(message=message, tool_calls=tool_calls)

        if not snapshot:
            return []

        mode = str(snapshot.get("mode") or "create")
        content = _interactivity_content()
        chips_by_mode = content.get("sqlAdvancedChips") or {}
        labels = chips_by_mode.get(mode) or chips_by_mode.get("default") or []
        queries = content.get("sqlAdvancedQueries") or {}
        workspace = snapshot.get("workspace") if isinstance(snapshot.get("workspace"), dict) else {}
        table_name = (workspace.get("tableNames") or ["{{tableName}}"])[0]
        result_analysis = (
            snapshot.get("resultAnalysis") if isinstance(snapshot.get("resultAnalysis"), dict) else None
        )
        visualization = (
            snapshot.get("visualizationAdvice")
            if isinstance(snapshot.get("visualizationAdvice"), dict)
            else None
        )
        suggestions: list[dict[str, str]] = []

        if isinstance(result_analysis, dict) and result_analysis.get("isEmpty"):
            from app.domain.services.chat_sql_result_analyzer_service import (
                ChatSqlResultAnalyzerService,
            )

            suggestions.extend(ChatSqlResultAnalyzerService.build_empty_recovery_follow_ups())

        for label in labels:
            if not isinstance(label, str) or not label.strip():
                continue

            template = queries.get(label, label)
            query = template.replace("{{tableName}}", table_name)

            suggestions.append({"label": label, "query": query})

        if visualization and isinstance(visualization.get("suggestedLabel"), str):
            label = str(visualization["suggestedLabel"]).strip()
            query = queries.get(label, f"gere um gráfico com os dados da última consulta")

            if label and not any(item.get("label") == label for item in suggestions):
                suggestions.insert(0, {"label": label, "query": query})

        return suggestions

