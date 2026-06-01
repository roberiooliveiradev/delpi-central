"""Resolução de dialeto SQL — Playbook Especialista SQL Avançado §10."""

from __future__ import annotations

from typing import Literal

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

SqlDialect = Literal[
    "sqlserver",
    "postgresql",
    "mysql",
    "oracle",
    "sqlite",
    "generic",
]

_DIALECT_HINTS: tuple[tuple[str, SqlDialect], ...] = (
    ("sql server", "sqlserver"),
    ("sqlserver", "sqlserver"),
    ("mssql", "sqlserver"),
    ("tsql", "sqlserver"),
    ("t-sql", "sqlserver"),
    ("protheus", "sqlserver"),
    ("totvs", "sqlserver"),
    ("postgres", "postgresql"),
    ("postgresql", "postgresql"),
    ("pgsql", "postgresql"),
    ("mysql", "mysql"),
    ("mariadb", "mysql"),
    ("oracle", "oracle"),
    ("plsql", "oracle"),
    ("sqlite", "sqlite"),
)


class ChatSqlDialectResolverService:
    @classmethod
    def default_dialect(cls) -> SqlDialect:
        from app.infrastructure.config.settings import Settings

        token = str(Settings.CHAT_DEFAULT_SQL_DIALECT or "sqlserver").strip().lower()

        if token in {"sqlserver", "postgresql", "mysql", "oracle", "sqlite", "generic"}:
            return token  # type: ignore[return-value]

        return "sqlserver"

    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
    ) -> dict[str, str | bool]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        detected: SqlDialect | None = None
        source = "default"

        if normalized:
            for hint, dialect in _DIALECT_HINTS:
                if hint in normalized:
                    detected = dialect
                    source = "message"
                    break

        if detected is None and isinstance(workspace_context, dict):
            configured = workspace_context.get("sqlDialect")

            if isinstance(configured, str) and configured.strip():
                detected = configured.strip().lower()  # type: ignore[assignment]
                source = "workspace"

        dialect = detected or cls.default_dialect()
        assumed = detected is None

        return {
            "dialect": dialect,
            "source": source,
            "assumed": assumed,
            "limitSyntax": cls.limit_syntax(dialect),
            "dateSyntaxHint": cls.date_syntax_hint(dialect),
        }

    @classmethod
    def limit_syntax(cls, dialect: str) -> str:
        if dialect == "sqlserver":
            return "TOP n"

        if dialect == "oracle":
            return "FETCH FIRST n ROWS ONLY"

        return "LIMIT n"

    @classmethod
    def date_syntax_hint(cls, dialect: str) -> str:
        if dialect == "sqlserver":
            return "DATEADD, DATEDIFF, GETDATE()"

        if dialect == "postgresql":
            return "DATE_TRUNC, INTERVAL, NOW()"

        if dialect == "mysql":
            return "DATE_FORMAT, DATE_SUB, NOW()"

        if dialect == "oracle":
            return "TRUNC, ADD_MONTHS, SYSDATE"

        return "funções de data do dialeto escolhido"
