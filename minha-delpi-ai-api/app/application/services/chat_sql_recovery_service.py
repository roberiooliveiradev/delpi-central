"""Orquestra consulta de schema e nova tentativa de POST /data/sql."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_sql_error_recovery_service import (
    ChatSqlErrorRecoveryService,
    SqlRecoveryPlan,
)


@dataclass(frozen=True)
class SqlRecoveryAttempt:
    failed_metadata: dict
    failed_arguments: dict
    schema_metadata: dict
    schema_data: object
    retry_metadata: dict
    retry_data: object
    plan: SqlRecoveryPlan


class ChatSqlRecoveryService:
    def __init__(
        self,
        execute_tool_use_case: ExecuteToolUseCase,
        external_action_repository=None,
    ):
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_repository = external_action_repository

    def maybe_recover(
        self,
        *,
        user_id: str,
        access_token: str,
        allowed_action_ids: list[str] | None,
        arguments: dict,
        metadata: dict,
        reason: str | None = None,
        on_stream_activity=None,
    ) -> SqlRecoveryAttempt | None:
        if not allowed_action_ids or not self.external_action_repository:
            return None

        path = str(metadata.get("path") or "")
        if not ChatSqlErrorRecoveryService.is_recoverable_sql_failure(metadata, path=path):
            return None

        invalid_column = ChatSqlErrorRecoveryService.parse_invalid_column(metadata)
        original_sql = ChatSqlErrorRecoveryService.extract_sql_from_arguments(arguments)

        if not invalid_column or not original_sql:
            return None

        table_name = ChatSqlErrorRecoveryService.infer_table_for_column(
            original_sql,
            invalid_column,
        )
        if not table_name:
            return None

        schema_action = self._resolve_table_schema_action(
            table_name=table_name,
            allowed_action_ids=allowed_action_ids,
        )
        if not schema_action:
            return None

        schema_result = self._execute_external_action(
            user_id=user_id,
            access_token=access_token,
            action_id=str(schema_action["actionId"]),
            arguments={"parameters": {"tableName": table_name}},
            on_stream_activity=on_stream_activity,
            path_hint=str(schema_action.get("path") or ""),
        )
        schema_metadata = dict(schema_result.metadata or {})

        if not schema_metadata.get("ok"):
            return None

        plan = ChatSqlErrorRecoveryService.build_recovery_plan(
            sql=original_sql,
            invalid_column=invalid_column,
            schema_payload=schema_result.data,
        )
        if not plan:
            return None

        sql_action = self._resolve_data_sql_action(allowed_action_ids)
        if not sql_action:
            return None

        retry_body = {
            "query": plan.corrected_sql,
            "sql": plan.corrected_sql,
            "statement": plan.corrected_sql,
        }
        retry_result = self._execute_external_action(
            user_id=user_id,
            access_token=access_token,
            action_id=str(sql_action["actionId"]),
            arguments={"body": retry_body},
            on_stream_activity=on_stream_activity,
            path_hint="/data/sql",
        )
        retry_metadata = dict(retry_result.metadata or {})

        if not retry_metadata.get("ok"):
            return None

        return SqlRecoveryAttempt(
            failed_metadata=dict(metadata),
            failed_arguments=dict(arguments),
            schema_metadata=schema_metadata,
            schema_data=schema_result.data,
            retry_metadata=retry_metadata,
            retry_data=retry_result.data,
            plan=plan,
        )

    def _execute_external_action(
        self,
        *,
        user_id: str,
        access_token: str,
        action_id: str,
        arguments: dict,
        on_stream_activity=None,
        path_hint: str = "",
    ) -> ToolResult:
        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.tool_started(
                    index=1,
                    total=1,
                    path=path_hint or None,
                    action_id=action_id,
                    reason="Recuperação automática de SQL com schema Protheus.",
                )
            )

        result = self.execute_tool_use_case.execute(
            ExecuteToolRequest(
                user_id=user_id,
                access_token=access_token,
                tool_name="execute_external_action",
                arguments={"actionId": action_id, **arguments},
            )
        )

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.tool_finished(
                    index=1,
                    total=1,
                    metadata=dict(result.metadata or {}),
                    path=str((result.metadata or {}).get("path") or path_hint or "") or None,
                    action_id=action_id,
                    data=result.data,
                )
            )

        return ToolResult(
            name=result.name,
            data=result.data,
            metadata=result.metadata,
        )

    def _resolve_table_schema_action(
        self,
        *,
        table_name: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        allowed = {str(item) for item in allowed_action_ids}
        candidates = [
            action
            for action in self.external_action_repository.find_candidate_actions(
                f"schema tabela {table_name}",
                limit=120,
                allowed_action_ids=allowed_action_ids,
            )
            if str(action.get("actionId") or "") in allowed
            and str(action.get("method") or "").upper() == "GET"
        ]

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            value = 0
            if "/tables/" in path and "/schema" in path:
                value += 120
            if "/tables/" in path and path.endswith("/columns"):
                value += 100
            if table_name.lower() in path:
                value += 40
            return value

        ranked = sorted(candidates, key=score, reverse=True)
        if not ranked or score(ranked[0]) <= 0:
            return None

        return ranked[0]

    def _resolve_data_sql_action(self, allowed_action_ids: list[str]) -> dict | None:
        allowed = {str(item) for item in allowed_action_ids}

        list_actions = getattr(self.external_action_repository, "list_actions", None)
        if callable(list_actions):
            for action in list_actions():
                if str(action.get("actionId") or "") not in allowed:
                    continue
                if "/data/sql" in str(action.get("path") or "").lower():
                    return action

        for action in self.external_action_repository.find_candidate_actions(
            "/data/sql execute readonly",
            limit=120,
            allowed_action_ids=list(allowed_action_ids),
        ):
            if str(action.get("actionId") or "") not in allowed:
                continue
            if "/data/sql" in str(action.get("path") or "").lower():
                return action

        return None
