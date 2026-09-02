"""Compat: reexporta o cache unificado de despesas por CC."""

from app.application.services.financeiro_despesas_centro_custo.despesas_centro_custo_query_cache import (  # noqa: F401
    get_cached_ranking_rows,
    ranking_centros_cache_key,
    ranking_fornecedores_cache_key,
    set_cached_ranking_rows,
)
