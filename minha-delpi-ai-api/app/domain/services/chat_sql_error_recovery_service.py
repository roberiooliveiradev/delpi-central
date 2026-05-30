"""Recuperação automática de SQL inválido via metadados Protheus (/system/tables)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_INVALID_COLUMN_RE = re.compile(
    r"Invalid column name\s+'([^']+)'",
    re.IGNORECASE,
)
_TABLE_FROM_SQL_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Z0-9_]+)(?:\s+(?:AS\s+)?([A-Z_][A-Z0-9_]*))?",
    re.IGNORECASE,
)
_QUALIFIED_COLUMN_RE = re.compile(
    r"\b([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\b",
    re.IGNORECASE,
)
_PROTHEUS_TABLE_FROM_FIELD_RE = re.compile(r"^([A-Z]\d+)_")


@dataclass(frozen=True)
class SqlRecoveryPlan:
    invalid_column: str
    table_name: str
    corrected_sql: str
    replacement_column: str
    reason: str


class ChatSqlErrorRecoveryService:
    MAX_REPLACEMENTS = 3

    @classmethod
    def is_recoverable_sql_failure(cls, metadata: dict | None, *, path: str = "") -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get("ok"):
            return False

        resolved_path = str(metadata.get("path") or path or "").lower()
        if "/data/sql" not in resolved_path:
            return False

        return cls.parse_invalid_column(metadata) is not None

    @classmethod
    def parse_invalid_column(cls, metadata: dict) -> str | None:
        preview = str(metadata.get("responsePreview") or "")
        match = _INVALID_COLUMN_RE.search(preview)

        if match:
            return match.group(1).upper()

        for source in (
            preview,
            json.dumps(metadata.get("textPresentation") or {}, ensure_ascii=False),
        ):
            match = _INVALID_COLUMN_RE.search(source)
            if match:
                return match.group(1).upper()

        return None

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
    def build_table_aliases(cls, sql: str) -> dict[str, str]:
        aliases: dict[str, str] = {}

        for match in _TABLE_FROM_SQL_RE.finditer(sql or ""):
            table = match.group(1).upper()
            alias = (match.group(2) or table).upper()
            aliases[alias] = table
            aliases[table] = table

        return aliases

    @classmethod
    def infer_table_for_column(cls, sql: str, column: str) -> str | None:
        upper_column = column.upper()
        aliases = cls.build_table_aliases(sql)

        for alias, field in _QUALIFIED_COLUMN_RE.findall(sql or ""):
            if field.upper() != upper_column:
                continue

            table = aliases.get(alias.upper())
            if table:
                return table

        prefix_match = _PROTHEUS_TABLE_FROM_FIELD_RE.match(upper_column)
        if prefix_match:
            return f"S{prefix_match.group(1)}010"

        return None

    @classmethod
    def extract_column_names(cls, payload: Any) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()

        def visit(node: Any) -> None:
            if isinstance(node, dict):
                for key in ("X3_CAMPO", "x3_campo", "column_name", "columnName", "field"):
                    value = node.get(key)
                    if value:
                        upper = str(value).upper()
                        if upper not in seen:
                            seen.add(upper)
                            names.append(upper)

                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(payload)
        return names

    @classmethod
    def resolve_replacement_column(
        cls,
        invalid_column: str,
        available_columns: list[str],
    ) -> str | None:
        invalid = invalid_column.upper()
        columns = [str(item).upper() for item in available_columns if str(item).strip()]

        if invalid in columns:
            return invalid

        prefix_matches = sorted(
            {column for column in columns if column.startswith(invalid)},
            key=len,
        )
        if len(prefix_matches) == 1:
            return prefix_matches[0]

        if prefix_matches:
            return prefix_matches[0]

        field_prefix_match = _PROTHEUS_TABLE_FROM_FIELD_RE.match(invalid)
        if field_prefix_match:
            field_prefix = field_prefix_match.group(1)
            scoped = [
                column
                for column in columns
                if column.startswith(f"{field_prefix}_")
            ]
            if len(scoped) == 1:
                return scoped[0]

        return None

    @classmethod
    def replace_column_in_sql(
        cls,
        sql: str,
        *,
        invalid_column: str,
        replacement_column: str,
    ) -> str:
        invalid = invalid_column.upper()
        replacement = replacement_column.upper()
        updated = sql

        for alias, field in _QUALIFIED_COLUMN_RE.findall(sql):
            if field.upper() != invalid:
                continue
            updated = re.sub(
                rf"\b{re.escape(alias)}\.{re.escape(field)}\b",
                f"{alias}.{replacement}",
                updated,
                flags=re.IGNORECASE,
            )

        updated = re.sub(
            rf"\b{re.escape(invalid)}\b",
            replacement,
            updated,
            flags=re.IGNORECASE,
        )
        return updated

    @classmethod
    def build_recovery_plan(
        cls,
        *,
        sql: str,
        invalid_column: str,
        schema_payload: Any,
    ) -> SqlRecoveryPlan | None:
        table_name = cls.infer_table_for_column(sql, invalid_column)
        if not table_name:
            return None

        available_columns = cls.extract_column_names(schema_payload)
        replacement = cls.resolve_replacement_column(invalid_column, available_columns)
        if not replacement or replacement.upper() == invalid_column.upper():
            return None

        corrected_sql = cls.replace_column_in_sql(
            sql,
            invalid_column=invalid_column,
            replacement_column=replacement,
        )

        if corrected_sql.strip() == sql.strip():
            return None

        return SqlRecoveryPlan(
            invalid_column=invalid_column.upper(),
            table_name=table_name,
            corrected_sql=corrected_sql,
            replacement_column=replacement.upper(),
            reason=(
                f"Coluna inválida `{invalid_column}` corrigida para `{replacement}` "
                f"com base no schema de `{table_name}`."
            ),
        )
