"""Perguntas operacionais que exigem SQL analítico (docs do agente), não catálogo REST."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_PRODUCTION_SQL_PHRASES = (
    "produzidos hoje",
    "produzido hoje",
    "serao produzidos",
    "sera produzido",
    "vao ser produzidos",
    "vao ser produzido",
    "producao de hoje",
    "producao hoje",
    "programacao de producao",
    "programacao produtiva",
    "ordens de producao",
    "ordem de producao",
    "planejamento de producao",
    "lista de producao",
    "apontamento de producao",
    "sc2010",
)

_CATALOG_SEARCH_MARKERS = (
    "busque produto",
    "pesquise produto",
    "procure produto",
    "encontre produto",
    "cadastro de produto",
    "descricao do produto",
    "codigo do produto",
    "informacoes sobre o produto",
)

_TEMPORAL_TERMS = ("hoje", "amanha", "semana", "mes ", "proxim")


class ChatSqlOperationalIntentService:
    @classmethod
    def requires_sql_knowledge(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in _CATALOG_SEARCH_MARKERS):
            return False

        if any(phrase in normalized for phrase in _PRODUCTION_SQL_PHRASES):
            return True

        if re.search(r"\bproduz\w*\b", normalized) and any(
            term in normalized for term in _TEMPORAL_TERMS
        ):
            if "quais produtos" in normalized or "que produtos" in normalized:
                return True

        return False
