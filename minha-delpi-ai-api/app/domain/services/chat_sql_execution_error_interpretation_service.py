"""Interpretação de erros ODBC/SQL Server para mensagens do chat."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SqlErrorInterpretation:
    error_type: str
    summary: str
    reasons: list[str]


class ChatSqlExecutionErrorInterpretationService:
    _INVALID_OBJECT_RE = re.compile(
        r"invalid object name\s+'([^']+)'",
        re.IGNORECASE,
    )

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

        if cls._looks_like_invalid_object(lowered):
            object_name = cls._extract_invalid_object_name(text)
            summary = (
                "O banco não reconheceu a tabela ou view usada na consulta."
                if not object_name
                else (
                    f"O banco não reconheceu o objeto `{object_name}` "
                    "(tabela ou view) na consulta."
                )
            )
            reasons = [
                "nome físico diferente do ambiente (sufixo Protheus, ex.: SA1010)",
                "objeto ainda não existe nesta base de dados",
            ]

            if object_name and object_name != object_name.upper():
                reasons.append(
                    "identificadores em minúsculas em banco com collation case-sensitive"
                )

            return SqlErrorInterpretation(
                error_type="sql_invalid_object",
                summary=summary,
                reasons=reasons,
            )

        if cls._looks_like_syntax_error(lowered):
            return SqlErrorInterpretation(
                error_type="sql_syntax_error",
                summary=(
                    "A consulta enviada ao banco tem erro de sintaxe. "
                    "Revise literais, aspas e cláusulas antes de executar de novo."
                ),
                reasons=[
                    "literal incompleto após operador (ex.: = sem valor)",
                    "vírgula, parêntese ou palavra-chave faltando",
                    "dialeto SQL Server / Protheus diferente do esperado",
                ],
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
                summary=(
                    "A consulta não foi concluída a tempo ou houve falha de conexão com o banco."
                ),
                reasons=[
                    "carga elevada ou consulta muito pesada",
                    "instabilidade momentânea na conexão com o SQL Server",
                ],
            )

        if any(
            token in lowered
            for token in ("permission", "denied", "not authorized", "unauthorized")
        ):
            return SqlErrorInterpretation(
                error_type="permission_denied",
                summary="A consulta foi recusada por falta de permissão no banco ou na API.",
                reasons=[
                    "usuário sem permissão para o objeto consultado",
                    "action ou perfil sem acesso a esta operação",
                ],
            )

        if any(
            token in lowered
            for token in ("odbc", "sql server", "sqlstate", "sqlexec")
        ):
            return SqlErrorInterpretation(
                error_type="sql_execution_error",
                summary=(
                    "O banco retornou um erro ao executar a consulta. "
                    "Revise tabelas, colunas e filtros antes de tentar de novo."
                ),
                reasons=[
                    "restrição ou regra do banco não atendida pela consulta",
                    "tipo de dado ou função incompatível com o SQL enviado",
                ],
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
            return (
                "Não foi possível executar a consulta SQL neste ambiente. "
                "Revise tabelas e colunas Protheus e tente novamente."
            )

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
