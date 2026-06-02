"""Descoberta de schema SQL e metadados via mensagem e tool calls.

Playbook Especialista SQL Avançado §14–15.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_TABLE_CODE_RE = re.compile(r"\b([A-Za-z]{2,4}\d{1,4})\b")
_COLUMN_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,40}\b")
_COLUMN_HINT_PATTERNS = (
    r"\bcolunas?\s+de\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
    r"\bcampos?\s+de\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
    r"\bcoluna[s]?\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
    r"\bcampo[s]?\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
)

_VALID_WORD_RE = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]{2,40})\b")


class ChatSqlSchemaDiscoveryService:
    @classmethod
    def extract_table_candidates(cls, message: str | None) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return []

        candidate_tables: list[str] = []

        for match in _TABLE_CODE_RE.finditer(str(message or "")):
            code = match.group(1).upper()

            if code not in candidate_tables:
                candidate_tables.append(code)

        return candidate_tables

    @classmethod
    def extract_column_candidates(cls, message: str | None) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return []

        candidates: list[str] = []
        seen: set[str] = set()
        raw = str(message or "")

        for match in _COLUMN_IDENTIFIER_RE.finditer(raw):
            token = match.group(0).strip().upper()

            if token not in seen:
                seen.add(token)
                candidates.append(token)

        for pattern in _COLUMN_HINT_PATTERNS:
            for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
                field = match.group(1).strip().upper()

                if field and field not in seen:
                    seen.add(field)
                    candidates.append(field)

        return candidates

    @classmethod
    def extract_domain_hint(cls, message: str | None) -> str | None:
        if not message:
            return None

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        return ChatSqlAuthoringGuidanceService.extract_domain_hint(message)

    @classmethod
    def collect_schema_metadata(cls, tool_calls: list | None) -> dict[str, Any]:
        if not tool_calls:
            return {}

        schema: dict[str, Any] = {
            "tables": {},
            "relations": [],
            "searchResults": [],
        }

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "").lower()
            payload = cls._resolve_payload(tool_call, metadata)

            if payload is None:
                continue

            if "/tables/search" in path:
                schema["searchResults"].extend(cls._parse_table_search_results(payload))
                continue

            table_name = cls._extract_table_name_from_path(path)

            if not table_name:
                continue

            if "/columns" in path or "/schema" in path:
                columns = cls._parse_column_results(payload)

                if columns:
                    schema["tables"].setdefault(table_name, {})["columns"] = columns

            if "/relations" in path or "/schema" in path:
                relations = cls._parse_relation_results(payload)

                if relations:
                    schema["relations"].extend(relations)

        return schema

    @classmethod
    def build_schema_snapshot(
        cls,
        *,
        message: str | None = None,
        tool_calls: list | None = None,
    ) -> dict[str, Any]:
        return {
            "tableCandidates": cls.extract_table_candidates(message),
            "columnCandidates": cls.extract_column_candidates(message),
            "domainHint": cls.extract_domain_hint(message),
            "metadata": cls.collect_schema_metadata(tool_calls),
        }

    @classmethod
    def _resolve_payload(cls, tool_call: dict, metadata: dict) -> dict | None:
        for source in (
            tool_call.get("result"),
            tool_call.get("data"),
            metadata.get("responseData"),
            metadata.get("data"),
            metadata.get("result"),
        ):
            if isinstance(source, dict):
                return source

        return None

    @classmethod
    def _extract_table_name_from_path(cls, path: str) -> str | None:
        segments = [segment for segment in path.strip("/").split("/") if segment]

        if len(segments) >= 3 and segments[0] == "system" and segments[1] == "tables":
            return segments[2].upper()

        return None

    @classmethod
    def _parse_column_results(cls, payload: dict) -> list[dict[str, str]]:
        results = []

        for source_key in ("results", "columns", "fields"):
            raw = payload.get(source_key)

            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue

                    field = (
                        item.get("X3_CAMPO")
                        or item.get("column_name")
                        or item.get("field")
                        or item.get("name")
                    )
                    label = (
                        item.get("X3_DESCRIC")
                        or item.get("column_description")
                        or item.get("label")
                    )

                    if not field or not isinstance(field, str):
                        continue

                    result = {"field": field.strip().upper()}

                    if label and isinstance(label, str):
                        result["description"] = label.strip()

                    if result not in results:
                        results.append(result)

                if results:
                    return results

        return []

    @classmethod
    def _parse_table_search_results(cls, payload: dict) -> list[dict[str, str]]:
        results = []
        raw = payload.get("results")

        if not isinstance(raw, list):
            return results

        for item in raw:
            if not isinstance(item, dict):
                continue

            table_code = (
                item.get("X2_ARQUIVO")
                or item.get("table_name")
                or item.get("name")
            )
            description = (
                item.get("X2_NOME")
                or item.get("description")
                or item.get("title")
            )

            if not table_code or not isinstance(table_code, str):
                continue

            results.append(
                {
                    "table": table_code.strip().upper(),
                    "description": str(description).strip() if description else "",
                }
            )

        return results

    @classmethod
    def _parse_relation_results(cls, payload: dict) -> list[dict[str, str]]:
        relations: list[dict[str, str]] = []
        raw = payload.get("results") or payload.get("relations")

        if not isinstance(raw, list):
            return relations

        for item in raw:
            if not isinstance(item, dict):
                continue

            origin = (
                item.get("X9_DOM")
                or item.get("source_table")
                or item.get("origin_table")
                or item.get("table_name")
            )
            origin_field = (
                item.get("X9_CAMPO")
                or item.get("source_field")
                or item.get("origin_column")
                or item.get("field")
            )
            target = (
                item.get("X9_TABELA")
                or item.get("target_table")
                or item.get("destination_table")
            )
            target_field = (
                item.get("X9_CAMPO_DESTINO")
                or item.get("target_field")
                or item.get("destination_field")
            )

            if not origin or not origin_field or not target or not target_field:
                continue

            relations.append(
                {
                    "sourceTable": str(origin).strip().upper(),
                    "sourceField": str(origin_field).strip().upper(),
                    "targetTable": str(target).strip().upper(),
                    "targetField": str(target_field).strip().upper(),
                }
            )

        return relations
