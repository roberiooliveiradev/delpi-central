"""Seleção de actions OpenAPI SQL/data — Fase 3B lote 6."""

from __future__ import annotations

import re
from typing import Callable

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)


class ExternalActionSqlRouteSelectionService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def select(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
        selection_reason_key: str | None = None,
        raw_message: str | None = None,
        candidates_loader: Callable | None = None,
        rank_candidates: Callable | None = None,
    ) -> dict | None:
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatSqlSafetyService.contains_destructive_sql(sql):
            return None

        if not allowed_action_ids:
            return None

        # Sempre a action de SQL — nunca rank semântico de rotas REST (ex.: schedule/today).
        action = self._resolve_data_sql_action(allowed_action_ids)

        if not action:
            return None

        sql_query = (sql or "").strip() or self._extract_sql_query(
            str(raw_message or message).strip()
        )

        if not sql_query:
            from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
            from app.domain.services.chat_sql_executable_synthesis_service import (
                ChatSqlExecutableSynthesisService,
            )

            source = str(raw_message or message).strip()

            if ChatSqlIntentService.should_auto_execute_sql(source):
                synthesized = ChatSqlExecutableSynthesisService.synthesize_select(
                    source,
                    invent_default_table=False,
                )

                if synthesized and self._is_executable_select_candidate(synthesized):
                    sql_query = synthesized

        if not sql_query:
            return None

        if ChatSqlSafetyService.contains_destructive_sql(sql_query):
            return None

        body = ExternalActionSqlCapabilityService.build_sql_request_body(sql_query)

        reason = ExternalActionResponseContentService.get(
            "selectionReasons",
            selection_reason_key or ("productionSqlFastPath" if sql else "genericSql"),
        )

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "body": body,
            },
            "reason": reason,
        }

    def _extract_sql_query(self, message: str) -> str | None:
        raw = str(message or "").strip()

        quoted = re.search(r'["“](.+?)["”]', raw, flags=re.S)

        if quoted:
            return quoted.group(1).strip()

        marker = re.search(r"sql\s*:\s*(.+)$", raw, flags=re.I | re.S)

        if marker:
            return ExternalActionSqlCapabilityService.normalize_extracted_sql(marker.group(1))

        execute_match = re.search(r"execute\s*:\s*(.+)$", raw, flags=re.I | re.S)

        if execute_match:
            candidate = execute_match.group(1).strip()

            if re.search(r"\bselect\b", candidate, flags=re.I):
                return ExternalActionSqlCapabilityService.normalize_extracted_sql(candidate)

        select_match = re.search(r"(select\s+.+)$", raw, flags=re.I | re.S)

        if select_match:
            candidate = ExternalActionSqlCapabilityService.normalize_extracted_sql(
                select_match.group(1)
            )

            if candidate and self._is_executable_select_candidate(candidate):
                return candidate

        return None

    @staticmethod
    def _is_executable_select_candidate(sql: str) -> bool:
        """Exige SELECT…FROM com tabela — rejeita prosa «select top 10 de produtos…»."""
        normalized = re.sub(r"\s+", " ", str(sql or "").strip().lower())

        if not normalized.startswith("select"):
            return False

        return bool(re.search(r"\bfrom\b\s+[a-z_][a-z0-9_]*", normalized))

    def _resolve_data_sql_action(self, allowed_action_ids: list[str]) -> dict | None:
        actions: list[dict] = []
        seen: set[str] = set()

        list_actions = getattr(self.repository, "list_actions", None)

        if callable(list_actions):
            for action in list_actions():
                action_id = str(action.get("actionId") or "")

                if action_id and action_id not in seen:
                    seen.add(action_id)
                    actions.append(action)

        for action in self.repository.find_candidate_actions(
            "sql execute readonly query data",
            limit=120,
            allowed_action_ids=list(allowed_action_ids),
        ):
            action_id = str(action.get("actionId") or "")

            if action_id and action_id not in seen:
                seen.add(action_id)
                actions.append(action)

        return ExternalActionSqlCapabilityService.pick_sql_execution_action(
            actions,
            allowed_action_ids=allowed_action_ids,
        )
