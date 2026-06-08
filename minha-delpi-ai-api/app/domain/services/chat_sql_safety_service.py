"""Bloqueio de SQL destrutivo — Playbook 08 (chat base)."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

_DESTRUCTIVE_TOKENS = re.compile(
    r"\b(delete|update|insert|drop|alter|truncate|merge|exec|execute)\b",
    flags=re.IGNORECASE,
)

_SQL_CONTEXT = re.compile(
    r"\b(select|from|where|sql|consulta|query|sc20\d{2}|/data/sql|protheus)\b",
    flags=re.IGNORECASE,
)

_NATURAL_SQL_EXECUTE_INTENT = re.compile(
    r"\b(essa consulta|esta consulta|consulta no banco|no banco|traga os dados|trazer os dados)\b",
    flags=re.IGNORECASE,
)


class ChatSqlSafetyService:
    @classmethod
    def looks_like_sql_payload(cls, text: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(text)

        if not normalized:
            return False

        return bool(_SQL_CONTEXT.search(normalized))

    @classmethod
    def contains_destructive_sql(cls, text: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(text)

        if not normalized or not _DESTRUCTIVE_TOKENS.search(normalized):
            return False

        if not cls.looks_like_sql_payload(normalized):
            return False

        if re.search(r"\bdelete\s+from\b", normalized, flags=re.IGNORECASE):
            return True

        if re.search(
            r"\b(update|insert|drop|alter|truncate|merge)\b",
            normalized,
            flags=re.IGNORECASE,
        ):
            return True

        if re.search(r"\b(exec|execute)\b", normalized, flags=re.IGNORECASE):
            if re.search(r"\bselect\b", normalized, flags=re.IGNORECASE):
                return False

            if _NATURAL_SQL_EXECUTE_INTENT.search(normalized):
                return False

            return True

        return False

    @classmethod
    def blocked_direct_answer(cls, message: str | None, *, sql: str | None = None) -> str | None:
        for candidate in (sql, message):
            if candidate and cls.contains_destructive_sql(candidate):
                return ExternalActionResponseContentService.get(
                    "security",
                    "destructiveSqlBlocked",
                    default=(
                        "Não executo comandos que alteram ou apagam dados (DELETE, UPDATE, "
                        "INSERT, DROP, etc.). Posso ajudar com uma consulta somente leitura (SELECT)."
                    ),
                )

        return None
