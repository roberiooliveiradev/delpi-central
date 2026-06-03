from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_EXECUTE_TERMS = (
    "execute ",
    "executa ",
    "executar ",
    "rode ",
    "rodar ",
    "roda ",
    "run ",
    "consulte ",
    "consultar ",
    "consulta no banco",
    "no banco de dados",
    "busque no banco",
    "traga os dados",
    "trazer os dados",
    "mostre os resultados",
    "exiba os resultados",
    "retorne os dados",
    "retornar os dados",
    "aplique a query",
    "aplica a query",
)

_AUTHORING_TERMS = (
    "monte ",
    "monta ",
    "crie ",
    "cria ",
    "gere ",
    "gera ",
    "escreva ",
    "escreve ",
    "elabore ",
    "elabora ",
    "construa ",
    "constrói ",
    "formula ",
    "formule ",
    "ajuste ",
    "ajusta ",
    "altere ",
    "altera ",
    "corrija ",
    "corrige ",
    "refine ",
    "refina ",
    "mude ",
    "muda ",
    "atualize ",
    "atualiza ",
    "melhore ",
    "melhora ",
    "otimize ",
    "otimiza ",
    "reescreva ",
    "reescreve ",
    "mostre a query",
    "mostra a query",
    "exiba a query",
    "exibe a query",
    "qual e a query",
    "qual é a query",
    "me mostre o sql",
    "me mostra o sql",
    "somente a query",
    "so a query",
    "só a query",
    "apenas a query",
    "nao execute",
    "não execute",
    "sem executar",
    "sem rodar",
)

_SQL_BUILD_CONTEXT = (
    "query que",
    "consulta que",
    "sql que",
    "select que",
)


class ChatSqlIntentService:
    """Diferencia elaborar/mostrar SQL de executar via action."""

    @classmethod
    def _has_sql_context(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in (
                "sql",
                "consulta",
                "query",
                "select",
                "tabela",
                "coluna",
                "join",
                "schema",
                " from ",
                "cte",
                " window ",
                "/data/sql",
            )
        ) or bool(
            re.search(
                r"\b(?:sa|sb|sc|sd|se|sf|sg|sh|si|sj|sk|sl|sm|sn|so|sp)[a-z]?\d{0,4}\b",
                normalized,
            )
        )

    @classmethod
    def is_sql_conversation_turn(cls, message: str | None) -> bool:
        """Turno de especialista SQL — não deve cair em text_task puro."""
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatSqlSafetyService.looks_like_sql_payload(message):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not cls._has_sql_context(normalized):
            return False

        if cls.is_authoring_request(message) or cls.should_auto_execute_sql(message):
            return True

        return any(
            term in normalized
            for term in (
                "monte",
                "monta",
                "crie",
                "gere",
                "elabore",
                "revise",
                "revisa",
                "explique",
                "otimize",
                "execute",
                "executar",
            )
        )

    @classmethod
    def router_sub_intent(cls, message: str | None) -> str | None:
        """Sub-intent SQL para o roteador (evita falso positivo em «sem executar»)."""
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if not (
            ChatSqlSafetyService.looks_like_sql_payload(message)
            or cls._has_sql_context(normalized)
            or bool(re.search(r"\bsql\b", normalized))
        ):
            return None

        if cls.is_authoring_request(message):
            if any(term in normalized for term in ("revise", "revisar", "review", "valida")):
                return "sql_review"

            if any(term in normalized for term in ("explique", "explicar", "explain")):
                return "sql_explain"

            return "sql_generate"

        if cls.should_auto_execute_sql(message):
            return "sql_execute"

        if any(term in normalized for term in ("revise", "revisar", "review")):
            return "sql_review"

        if any(term in normalized for term in ("explique", "explicar", "explain")):
            return "sql_explain"

        return "sql_generate"

    @classmethod
    def is_authoring_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(term in normalized for term in _AUTHORING_TERMS):
            return True

        if "query" in normalized or "consulta sql" in normalized or "sql" in normalized:
            if any(ctx in normalized for ctx in _SQL_BUILD_CONTEXT):
                return True

        return False

    @classmethod
    def should_auto_execute_sql(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return not cls.is_authoring_request(message)

        if any(term in normalized for term in _AUTHORING_TERMS):
            return False

        if cls._has_embedded_select(normalized):
            return True

        if any(term in normalized for term in _EXECUTE_TERMS):
            return True

        if "query" in normalized or "consulta sql" in normalized or "sql" in normalized:
            if any(ctx in normalized for ctx in _SQL_BUILD_CONTEXT):
                return False

        return False

    @classmethod
    def _has_embedded_select(cls, normalized: str) -> bool:
        return bool(re.search(r"\bselect\s+.+\bfrom\b", normalized, flags=re.I | re.S))
