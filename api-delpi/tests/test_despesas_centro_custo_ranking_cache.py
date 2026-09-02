from app.application.services.financeiro_despesas_centro_custo.despesas_centro_custo_query_cache import (
    lancamentos_count_cache_key,
    ranking_centros_cache_key,
    ranking_fornecedores_cache_key,
    resumo_cache_key,
)


def test_ranking_centros_cache_key_is_stable() -> None:
    key = ranking_centros_cache_key(
        start_date="20250601",
        end_date="20250630",
        branch="01",
        supplier_code=None,
        supplier_store=None,
        limit=10,
        exclude_mp_products=True,
    )

    assert key == "despesas-cc-query-v1|ranking-centros|20250601|20250630|01|||10|1"


def test_ranking_fornecedores_cache_key_includes_cost_center() -> None:
    key = ranking_fornecedores_cache_key(
        start_date="20250601",
        end_date="20250630",
        branch="02",
        cost_center="0101",
        limit=25,
        exclude_mp_products=False,
    )

    assert key == "despesas-cc-query-v1|ranking-fornecedores|20250601|20250630|02|0101|25|0"


def test_resumo_and_count_cache_keys_are_stable() -> None:
    resumo = resumo_cache_key(
        start_date="20250601",
        end_date="20250630",
        branch="01",
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
        exclude_mp_products=True,
    )
    count = lancamentos_count_cache_key(
        start_date="20250601",
        end_date="20250630",
        branch="01",
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
        search=None,
        exclude_mp_products=True,
    )

    assert resumo == "despesas-cc-query-v1|resumo|20250601|20250630|01||||1"
    assert count == "despesas-cc-query-v1|lancamentos-count|20250601|20250630|01|||||1"
