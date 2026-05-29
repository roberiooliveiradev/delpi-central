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
