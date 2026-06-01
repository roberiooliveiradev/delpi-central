"""Detecta e seleciona actions de execução SQL entre providers/actions autorizados."""

from __future__ import annotations

import re
from typing import Any

_SQL_PATH_MARKERS = (
    "/data/sql",
    "/sql",
    "/queries",
    "/query",
)

_SQL_OPERATION_MARKERS = (
    "execute_sql",
    "execute_readonly",
    "execute_readonly_sql",
    "readonly_sql",
    "run_sql",
    "data_sql",
)

_SQL_ACTION_ID_MARKERS = (
    "execute_readonly",
    "execute_sql",
    "readonly_sql",
    "run_sql",
    "data_sql",
    "/data/sql",
    ".data.",
)

_SCHEMA_PATH_MARKERS = ("/schema", "/columns")


class ExternalActionSqlCapabilityService:
    @classmethod
    def is_sql_execution_action(cls, action: dict | None) -> bool:
        if not isinstance(action, dict):
            return False

        method = str(action.get("method") or "").upper()
        path = str(action.get("path") or "").lower()
        sensitivity = str(action.get("sensitivity") or "").lower()
        operation_id = str(action.get("operationId") or "").lower()
        action_id = str(action.get("actionId") or "").lower()

        if sensitivity == "sql" and method in {"POST", "PUT", "PATCH"}:
            return True

        if method == "GET" and any(marker in path for marker in _SCHEMA_PATH_MARKERS):
            return False

        if any(marker in path for marker in _SQL_PATH_MARKERS):
            if method == "POST" or "execute" in path or path.rstrip("/").endswith("/sql"):
                return True

        combined = f"{operation_id} {action_id}"
        if any(marker in combined for marker in _SQL_OPERATION_MARKERS):
            return True

        return False

    @classmethod
    def is_sql_execution_context(
        cls,
        *,
        path: str | None = None,
        operation_id: str | None = None,
        action_id: str | None = None,
        sensitivity: str | None = None,
    ) -> bool:
        return cls.is_sql_execution_action(
            {
                "path": path or "",
                "operationId": operation_id or "",
                "actionId": action_id or "",
                "method": "POST",
                "sensitivity": sensitivity or "",
            }
        )

    @classmethod
    def is_sql_result_payload(cls, root: dict | None) -> bool:
        if not isinstance(root, dict):
            return False

        resultsets = root.get("resultsets")

        if isinstance(resultsets, list):
            return True

        return root.get("total_resultsets") is not None

    @classmethod
    def score_sql_execution_action(cls, action: dict) -> int:
        if not cls.is_sql_execution_action(action):
            return 0

        path = str(action.get("path") or "").lower()
        operation_id = str(action.get("operationId") or "").lower()
        action_id = str(action.get("actionId") or "").lower()
        sensitivity = str(action.get("sensitivity") or "").lower()
        score = 10

        if "/data/sql" in path:
            score += 120
        elif path.rstrip("/").endswith("/sql"):
            score += 90

        if sensitivity == "sql":
            score += 80

        if any(marker in operation_id for marker in _SQL_OPERATION_MARKERS):
            score += 70

        if any(marker in action_id for marker in _SQL_ACTION_ID_MARKERS):
            score += 60

        if str(action.get("method") or "").upper() == "POST":
            score += 10

        return score

    @classmethod
    def pick_sql_execution_action(
        cls,
        actions: list[dict] | None,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> dict | None:
        allowed = {str(item) for item in (allowed_action_ids or []) if str(item).strip()}
        ranked: list[tuple[int, dict]] = []

        for action in actions or []:
            if not isinstance(action, dict):
                continue

            action_id = str(action.get("actionId") or "")
            if allowed and action_id not in allowed:
                continue

            score = cls.score_sql_execution_action(action)
            if score > 0:
                ranked.append((score, action))

        if not ranked:
            return None

        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[0][1]

    @classmethod
    def allowed_action_ids_include_sql(cls, allowed_action_ids: list[str] | None) -> bool:
        for action_id in allowed_action_ids or []:
            lowered = str(action_id or "").lower()
            if any(token in lowered for token in _SQL_ACTION_ID_MARKERS):
                return True
            if re.search(r"(^|[._/])sql($|[._/])", lowered):
                return True

        return False

    @classmethod
    def build_sql_request_body(cls, sql: str) -> dict[str, str]:
        query = str(sql or "").strip()
        return {
            "query": query,
            "sql": query,
            "statement": query,
        }

    @classmethod
    def extract_sql_from_arguments(cls, arguments: dict | None) -> str | None:
        if not isinstance(arguments, dict):
            return None

        body = arguments.get("body")
        if isinstance(body, dict):
            for key in ("sql", "query", "statement"):
                value = str(body.get(key) or "").strip()
                if value:
                    return value

        for key in ("sql", "query", "statement"):
            value = str(arguments.get(key) or "").strip()
            if value:
                return value

        return None

    @classmethod
    def extract_sql_from_metadata(cls, metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        for key in ("executedSql", "sql", "query", "statement"):
            value = str(metadata.get(key) or "").strip()
            if value:
                return value

        return None

    @classmethod
    def attach_request_sql_to_data(
        cls,
        data: Any,
        *,
        arguments: dict | None = None,
        metadata: dict | None = None,
    ):
        sql_query = cls.extract_sql_from_arguments(arguments) or cls.extract_sql_from_metadata(
            metadata
        )

        if not sql_query or not isinstance(data, dict):
            return data

        enriched = dict(data)
        root = enriched.get("data", enriched)

        if isinstance(root, dict) and "data" in root and isinstance(root["data"], dict):
            nested = dict(root["data"])
            nested["sql"] = sql_query
            enriched["data"] = {**root, "data": nested}
            return enriched

        if isinstance(root, dict):
            nested = dict(root)
            nested["sql"] = sql_query
            if "data" in enriched and enriched["data"] is root:
                enriched["data"] = nested
            else:
                enriched = {**enriched, "data": nested}
            return enriched

        return data

    @classmethod
    def looks_like_production_schedule_sql(cls, sql: str | None) -> bool:
        text = str(sql or "").upper()
        if "SC2010" in text and "H8_DTINI" in text:
            return True
        return "@FILIAL" in text and "DECLARE @DATA DATE" in text and "C2_PRODUTO" in text

    @classmethod
    def looks_like_inventory_below_minimum_sql(cls, sql: str | None) -> bool:
        text = str(sql or "").upper()

        if "SB2010" not in text:
            return False

        return any(
            token in text
            for token in (
                "B1_EMIN",
                "BZ_ESTSEG",
                "MINIMUM_STOCK",
            )
        )
