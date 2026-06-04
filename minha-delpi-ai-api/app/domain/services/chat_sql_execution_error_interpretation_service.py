"""Interpretação de erros ODBC/SQL Server para mensagens do chat."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@dataclass(frozen=True)
class SqlErrorInterpretation:
    error_type: str
    summary: str
    reasons: list[str]


class ChatSqlExecutionErrorInterpretationService:
    _BUNDLE = "sql_execution_errors"
    _INVALID_OBJECT_RE = re.compile(
        r"invalid object name\s+'([^']+)'",
        re.IGNORECASE,
    )

    @classmethod
    def _handling_type(cls, internal_type: str) -> str:
        mapping = ChatAssistantContentService.get_mapping(cls._BUNDLE, "errorTypeToHandling")

        return mapping.get(internal_type, internal_type)

    @classmethod
    def _summary_for_type(cls, internal_type: str, **fmt) -> str:
        handling = cls._handling_type(internal_type)
        message = ChatAssistantContentService.get_error_type(handling, "userMessage")

        if message:
            return message

        return ChatAssistantContentService.get(cls._BUNDLE, "fallbackSummary")

    @classmethod
    def _reasons_for_type(cls, internal_type: str) -> list[str]:
        handling = cls._handling_type(internal_type)
        reasons = ChatAssistantContentService.get_error_reasons(handling)

        return reasons or []

    @classmethod
    def is_sql_execution_path(cls, path: str) -> bool:
        lowered = str(path or "").lower()
        return "/data/sql" in lowered

    @classmethod
    def extract_error_text(cls, data: Any) -> str:
        if data is None:
            return ""

        if isinstance(data, str):
            return data.strip()

        if not isinstance(data, dict):
            return str(data).strip()

        for key in ("message", "error", "detail", "errorMessage"):
            value = data.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        nested = data.get("data")

        if isinstance(nested, dict):
            nested_text = cls.extract_error_text(nested)

            if nested_text:
                return nested_text

        return ""

    @classmethod
    def has_logical_failure(cls, data: Any, *, path: str = "") -> bool:
        if not cls.is_sql_execution_path(path):
            return False

        root = cls._unwrap_payload(data)

        if not isinstance(root, dict):
            return False

        if root.get("success") is False:
            return bool(cls.extract_error_text(root))

        return False

    @classmethod
    def interpret(cls, error_text: str) -> SqlErrorInterpretation | None:
        text = str(error_text or "").strip()

        if not text:
            return None

        lowered = text.lower()

        if "empty body" in lowered and "sql not provided" in lowered:
            return SqlErrorInterpretation(
                error_type="sql_missing_body",
                summary=cls._summary_for_type("sql_missing_body"),
                reasons=cls._reasons_for_type("sql_missing_body"),
            )

        if cls._looks_like_invalid_object(lowered):
            object_name = cls._extract_invalid_object_name(text)
            summary = (
                ChatAssistantContentService.format(
                    cls._BUNDLE,
                    "invalidObjectSummaryNamed",
                    object_name=object_name,
                )
                if object_name
                else ChatAssistantContentService.get(cls._BUNDLE, "invalidObjectSummary")
            )
            reasons = list(cls._reasons_for_type("sql_invalid_object"))

            if object_name and object_name != object_name.upper():
                extra = ChatAssistantContentService.get(
                    cls._BUNDLE,
                    "invalidObjectReasonCaseSensitive",
                )

                if extra and extra not in reasons:
                    reasons.append(extra)

            return SqlErrorInterpretation(
                error_type="sql_invalid_object",
                summary=summary,
                reasons=reasons,
            )

        if cls._looks_like_syntax_error(lowered):
            return SqlErrorInterpretation(
                error_type="sql_syntax_error",
                summary=cls._summary_for_type("sql_syntax_error"),
                reasons=cls._reasons_for_type("sql_syntax_error"),
            )

        if any(
            token in lowered
            for token in (
                "login timeout",
                "timeout expired",
                "connection",
                "conexão",
                "conexao",
                "sqldriverconnect",
            )
        ):
            return SqlErrorInterpretation(
                error_type="timeout",
                summary=cls._summary_for_type("timeout"),
                reasons=cls._reasons_for_type("timeout"),
            )

        if any(
            token in lowered
            for token in ("permission", "denied", "not authorized", "unauthorized")
        ):
            return SqlErrorInterpretation(
                error_type="permission_denied",
                summary=cls._summary_for_type("permission_denied"),
                reasons=cls._reasons_for_type("permission_denied"),
            )

        if any(
            token in lowered
            for token in ("odbc", "sql server", "sqlstate", "sqlexec")
        ):
            return SqlErrorInterpretation(
                error_type="sql_execution_error",
                summary=cls._summary_for_type("sql_execution_error"),
                reasons=cls._reasons_for_type("sql_execution_error"),
            )

        return None

    @classmethod
    def interpret_from_payload(cls, data: Any, *, path: str = "") -> SqlErrorInterpretation | None:
        if not cls.is_sql_execution_path(path):
            return None

        return cls.interpret(cls.extract_error_text(data))

    @classmethod
    def user_facing_message(cls, error_text: str, *, path: str = "") -> str | None:
        if not cls.is_sql_execution_path(path):
            return None

        interpretation = cls.interpret(error_text)

        if interpretation:
            return interpretation.summary

        text = str(error_text or "").strip()

        if not text or cls._looks_like_raw_driver_dump(text):
            return ChatAssistantContentService.get(cls._BUNDLE, "fallbackSummary")

        return None

    @classmethod
    def _unwrap_payload(cls, data: Any) -> Any:
        root = data

        if isinstance(root, dict) and "data" in root:
            inner = root.get("data")

            if isinstance(inner, dict):
                return inner

        return root

    @classmethod
    def _looks_like_invalid_object(cls, lowered: str) -> bool:
        return any(
            token in lowered
            for token in (
                "invalid object name",
                "nome de objeto inválido",
                "42s02",
                "objeto inválido",
            )
        )

    @classmethod
    def _looks_like_syntax_error(cls, lowered: str) -> bool:
        return any(
            token in lowered
            for token in (
                "incorrect syntax",
                "syntax near",
                "syntax error",
                "42000",
                "sintaxe incorreta",
                "erro de sintaxe",
            )
        )

    @classmethod
    def _extract_invalid_object_name(cls, error_text: str) -> str | None:
        match = cls._INVALID_OBJECT_RE.search(error_text)

        if not match:
            return None

        name = str(match.group(1) or "").strip()

        return name or None

    @classmethod
    def is_raw_driver_dump(cls, text: str) -> bool:
        return cls._looks_like_raw_driver_dump(text)

    @classmethod
    def _looks_like_raw_driver_dump(cls, text: str) -> bool:
        lowered = text.lower()

        return (
            "odbc driver" in lowered
            or "sqlexecdirect" in lowered
            or lowered.startswith("500:")
            or "sqlstate" in lowered
        )
