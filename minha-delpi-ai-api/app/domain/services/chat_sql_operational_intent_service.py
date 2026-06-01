"""Perguntas operacionais que exigem SQL analítico (docs do agente), não catálogo REST."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_temporal_intent_service import ChatTemporalIntentService

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
    "programados para producao",
    "produtos programados",
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

# Consultas agregadas sem GET /products/{code}/… — rota via POST /data/sql + playbooks SQL.
_INVENTORY_AGGREGATE_MARKERS = (
    "estoque abaixo",
    "abaixo do minimo",
    "abaixo do mínimo",
    "saldo abaixo",
    "ruptura de estoque",
    "produtos com estoque",
    "liste os produtos com estoque",
    "lista de produtos com estoque",
    "itens com estoque abaixo",
)

_SALES_AGGREGATE_MARKERS = (
    "vendas por mes",
    "vendas por mês",
    "evolucao de vendas",
    "evolução de vendas",
    "faturamento por mes",
    "faturamento por mês",
    "faturamento do mes",
    "faturamento do mês",
    "ranking dos",
    "ranking de clientes",
    "ranking de cliente",
    "top 10 clientes",
    "top 5 clientes",
    "clientes que mais compraram",
    "participacao do faturamento",
    "participação do faturamento",
    "por cliente em rosca",
)

_TEMPORAL_TERMS = (
    "hoje",
    "ontem",
    "amanha",
    "anteontem",
    "semana",
    "mes ",
    "proxim",
    "passad",
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
)


class ChatSqlOperationalIntentService:
    @classmethod
    def requires_sql_knowledge(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in _CATALOG_SEARCH_MARKERS):
            return False

        if cls._looks_like_aggregate_sql_question(message, normalized):
            return True

        return cls.requires_production_sql_knowledge(message)

    @classmethod
    def requires_production_sql_knowledge(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in _CATALOG_SEARCH_MARKERS):
            return False

        if cls._looks_like_aggregate_sql_question(message, normalized):
            return False

        if any(phrase in normalized for phrase in _PRODUCTION_SQL_PHRASES):
            return True

        if re.search(r"\bproduz\w*\b", normalized) and (
            ChatTemporalIntentService.has_temporal_reference(message)
            or any(term in normalized for term in _TEMPORAL_TERMS)
        ):
            if any(
                phrase in normalized
                for phrase in (
                    "quais produtos",
                    "que produtos",
                    "o que",
                    "qual produto",
                    "produtos programados",
                )
            ):
                return True

        if (
            re.search(r"\bprogramad\w*\b", normalized)
            and re.search(r"\bproduc\w*\b", normalized)
        ):
            return True

        return False

    @classmethod
    def _looks_like_aggregate_sql_question(
        cls,
        message: str | None,
        normalized: str,
    ) -> bool:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if ChatProductQueryIntentService.extract_product_code(message):
            return False

        if ChatProductQueryIntentService.references_previous_product(message):
            return False

        if re.search(r"\bproduto\s+\d", normalized):
            return False

        if any(marker in normalized for marker in _INVENTORY_AGGREGATE_MARKERS):
            return True

        if any(marker in normalized for marker in _SALES_AGGREGATE_MARKERS):
            return True

        return False
