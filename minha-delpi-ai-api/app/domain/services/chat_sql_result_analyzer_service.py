"""Análise de resultados SQL executados — Playbook Especialista SQL §39, §46."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)


class ChatSqlResultAnalyzerService:
    @classmethod
    def _empty_recovery(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "resultAnalyzer",
            "emptyRecovery",
        )

    @classmethod
    def _execute_next_steps(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "resultAnalyzer",
            "executeNextSteps",
        )

    @classmethod
    def analyze_tool_calls(cls, tool_calls: list | None) -> dict[str, Any] | None:
        if not tool_calls:
            return None

        for tool_call in reversed(tool_calls):
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").lower()
            action_id = str(metadata.get("actionId") or "").lower()
            sensitivity = str(metadata.get("sensitivity") or "").lower()

            if path != "/data/sql" and "sql" not in action_id and sensitivity != "sql":
                continue

            payload = cls._resolve_payload(tool_call, metadata)
            analysis = cls.analyze_payload(payload, metadata=metadata)

            if analysis:
                return analysis

        return None

    @classmethod
    def analyze_payload(
        cls,
        payload: dict | None,
        *,
        metadata: dict | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None

        resultsets = cls._collect_resultsets(payload)
        row_count = cls._total_rows(resultsets)
        columns = cls._collect_columns(resultsets)
        is_empty = row_count == 0
        presentation = metadata.get("presentation") if isinstance(metadata, dict) else None
        presentation_type = None

        if isinstance(presentation, dict):
            presentation_type = str(presentation.get("type") or "").strip().lower() or None

        insights: list[str] = []

        if is_empty:
            insights.append(
                ChatSqlIntentVocabularyService.insight_text("empty")
            )
        elif row_count == 1:
            insights.append(
                ChatSqlIntentVocabularyService.insight_text("singleRow")
            )
        elif row_count <= 10:
            insights.append(
                ChatSqlIntentVocabularyService.insight_text(
                    "smallSet",
                    row_count=str(row_count),
                )
            )
        else:
            insights.append(
                ChatSqlIntentVocabularyService.insight_text(
                    "largeSet",
                    row_count=str(row_count),
                )
            )

        null_hints = cls._detect_nullable_columns(resultsets)

        if null_hints:
            insights.append(
                ChatSqlIntentVocabularyService.insight_text(
                    "nullableColumns",
                    columns=", ".join(null_hints[:4]),
                )
            )

        return {
            "rowCount": row_count,
            "isEmpty": is_empty,
            "columnCount": len(columns),
            "columns": columns[:12],
            "resultsetCount": len(resultsets),
            "presentationType": presentation_type,
            "insights": insights,
            "recoverySuggestions": list(cls._empty_recovery()) if is_empty else [],
            "nextSteps": list(cls._execute_next_steps()),
            "executedSql": cls._extract_executed_sql(payload, metadata),
        }

    @classmethod
    def build_empty_recovery_follow_ups(cls) -> list[dict[str, str]]:
        raw = ChatSqlIntentVocabularyService.node(
            "resultAnalyzer",
            "emptyRecoveryFollowUps",
        )

        if not isinstance(raw, list):
            return []

        follow_ups: list[dict[str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if label and query:
                follow_ups.append({"label": label, "query": query})

        return follow_ups

    @classmethod
    def _resolve_payload(cls, tool_call: dict, metadata: dict) -> dict | None:
        for source in (
            metadata.get("responseData"),
            metadata.get("data"),
            tool_call.get("result"),
            tool_call.get("data"),
        ):
            if isinstance(source, dict):
                nested = source.get("data")

                if isinstance(nested, dict) and nested.get("resultsets") is not None:
                    return nested

                if source.get("resultsets") is not None:
                    return source

        return metadata if metadata.get("resultsets") is not None else None

    @classmethod
    def _collect_resultsets(cls, payload: dict) -> list[dict]:
        raw = payload.get("resultsets")

        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]

        data = payload.get("data")

        if isinstance(data, dict) and isinstance(data.get("resultsets"), list):
            return [item for item in data["resultsets"] if isinstance(item, dict)]

        return []

    @classmethod
    def _total_rows(cls, resultsets: list[dict]) -> int:
        total = 0

        for resultset in resultsets:
            rows = resultset.get("data")

            if isinstance(rows, list):
                total += len(rows)
                continue

            count = resultset.get("total")

            if isinstance(count, int) and count >= 0:
                total += count

        return total

    @classmethod
    def _collect_columns(cls, resultsets: list[dict]) -> list[str]:
        columns: list[str] = []

        for resultset in resultsets:
            raw = resultset.get("columns")

            if not isinstance(raw, list):
                continue

            for item in raw:
                if isinstance(item, str) and item.strip():
                    columns.append(item.strip())
                elif isinstance(item, dict):
                    key = str(item.get("key") or item.get("label") or "").strip()

                    if key:
                        columns.append(key)

        deduped: list[str] = []

        for column in columns:
            if column not in deduped:
                deduped.append(column)

        return deduped

    @classmethod
    def _detect_nullable_columns(cls, resultsets: list[dict]) -> list[str]:
        nullable: list[str] = []

        for resultset in resultsets:
            rows = resultset.get("data")

            if not isinstance(rows, list) or not rows:
                continue

            columns = resultset.get("columns")

            if not isinstance(columns, list):
                continue

            for index, column in enumerate(columns):
                key = column if isinstance(column, str) else str(column.get("key") or "")

                if not key or key in nullable:
                    continue

                for row in rows[:20]:
                    value = None

                    if isinstance(row, dict):
                        value = row.get(key)
                    elif isinstance(row, (list, tuple)) and index < len(row):
                        value = row[index]

                    if value is None or value == "":
                        nullable.append(key)
                        break

        return nullable

    @classmethod
    def _extract_executed_sql(cls, payload: dict, metadata: dict | None) -> str | None:
        from app.domain.services.external_actions.external_action_sql_capability_service import (
            ExternalActionSqlCapabilityService,
        )

        for source in (payload, metadata or {}):
            if not isinstance(source, dict):
                continue

            sql = ExternalActionSqlCapabilityService.extract_sql_from_metadata(source)

            if sql:
                return sql

            sql = ExternalActionSqlCapabilityService.extract_sql_from_arguments(source)

            if sql:
                return sql

        return None
