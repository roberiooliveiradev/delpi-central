"""Memória de workspace SQL na sessão — Playbook Especialista SQL Avançado §43–45."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)


class ChatSqlMemoryWorkspaceService:
    _TABLE_RE = re.compile(r"\b(?:from|join)\s+([A-Za-z0-9_$.]+)", re.IGNORECASE)

    @classmethod
    def build_workspace(
        cls,
        *,
        message: str | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> dict[str, Any]:
        current_sql = cls.resolve_current_sql(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )
        tables = cls.extract_tables(current_sql) if current_sql else []

        return {
            "currentSql": current_sql,
            "tableNames": tables,
            "hasActiveQuery": bool(current_sql),
            "incrementalEditReady": bool(current_sql)
            and ChatSqlQueryRefinementService.is_sql_follow_up(
                str(message or ""),
                previous_messages=previous_messages,
            ),
        }

    @classmethod
    def resolve_current_sql(
        cls,
        *,
        message: str | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> str | None:
        from_message = ChatSqlPerformanceAdvisorService.extract_sql_block(message)

        if from_message:
            return from_message

        from_tools = cls._sql_from_tool_calls(tool_calls)

        if from_tools:
            return from_tools

        return cls._last_sql_from_history(previous_messages)

    @classmethod
    def _sql_from_tool_calls(cls, tool_calls: list | None) -> str | None:
        if not tool_calls:
            return None

        for tool_call in reversed(tool_calls):
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "").lower()

            if "/data/sql" not in path:
                continue

            arguments = tool_call.get("arguments")

            if isinstance(arguments, dict):
                body = arguments.get("body") or arguments.get("payload")

                if isinstance(body, dict):
                    sql = body.get("sql") or body.get("query")

                    if isinstance(sql, str) and sql.strip():
                        return sql.strip()

                sql = arguments.get("sql") or arguments.get("query")

                if isinstance(sql, str) and sql.strip():
                    return sql.strip()

        return None

    @classmethod
    def _last_sql_from_history(cls, previous_messages: list[Any] | None) -> str | None:
        if not previous_messages:
            return None

        authored_idx, authored_sql = cls._latest_authored_sql_index(previous_messages)
        executed_idx, executed_sql = cls._latest_executed_sql_index(previous_messages)

        if authored_sql and (authored_idx >= executed_idx or not executed_sql):
            return authored_sql

        if executed_sql:
            return executed_sql

        for msg in reversed(previous_messages):
            metadata = cls._message_metadata(msg)

            if isinstance(metadata, dict):
                workspace = metadata.get("sqlAdvanced")

                if isinstance(workspace, dict):
                    stored = workspace.get("workspace", workspace).get("currentSql")

                    if isinstance(stored, str) and stored.strip():
                        return stored.strip()

        return None

    @classmethod
    def _latest_authored_sql_index(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[int, str | None]:
        last_idx = -1
        last_sql: str | None = None

        for idx, msg in enumerate(previous_messages or []):
            content = cls._message_content(msg)
            sql = ChatSqlPerformanceAdvisorService.extract_sql_block(content)

            if sql:
                last_idx = idx
                last_sql = sql

        return last_idx, last_sql

    @classmethod
    def _latest_executed_sql_index(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[int, str | None]:
        from app.domain.services.external_actions.external_action_sql_capability_service import (
            ExternalActionSqlCapabilityService,
        )

        last_idx = -1
        last_sql: str | None = None

        for idx, msg in enumerate(previous_messages or []):
            metadata = cls._message_metadata(msg)

            if not isinstance(metadata, dict):
                continue

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if tool_meta.get("ok") is False:
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()
                sensitivity = str(tool_meta.get("sensitivity") or "").lower()

                if path != "/data/sql" and "sql" not in action_id and sensitivity != "sql":
                    continue

                sql = ExternalActionSqlCapabilityService.extract_sql_from_metadata(tool_meta)

                if not sql:
                    arguments = tool_call.get("arguments") or {}
                    body = arguments.get("body") or {}
                    sql = ExternalActionSqlCapabilityService.extract_sql_from_arguments(
                        {"body": body, **arguments}
                    )

                if sql:
                    last_idx = idx
                    last_sql = sql
                    break

        return last_idx, last_sql

    @classmethod
    def extract_tables(cls, sql: str | None) -> list[str]:
        if not sql:
            return []

        seen: set[str] = set()
        output: list[str] = []

        for match in cls._TABLE_RE.finditer(sql):
            name = match.group(1).strip().strip('"').strip("'").strip("[]")

            if not name or name.lower() in {"select", "where", "on"}:
                continue

            token = name.upper()

            if token in seen:
                continue

            seen.add(token)
            output.append(token)

        return output

    @classmethod
    def _message_content(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @classmethod
    def _message_metadata(cls, message: Any) -> dict | None:
        if isinstance(message, dict):
            metadata = message.get("metadata")

            return metadata if isinstance(metadata, dict) else None

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else None
