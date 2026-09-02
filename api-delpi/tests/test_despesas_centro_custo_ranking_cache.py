from app.application.services.financeiro_despesas_centro_custo.despesas_centro_custo_ranking_cache import (
    ranking_centros_cache_key,
    ranking_fornecedores_cache_key,
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

    assert key == "despesas-cc-ranking-v1|centros|20250601|20250630|01|||10|1"


def test_ranking_fornecedores_cache_key_includes_cost_center() -> None:
    key = ranking_fornecedores_cache_key(
        start_date="20250601",
        end_date="20250630",
        branch="02",
        cost_center="0101",
        limit=25,
        exclude_mp_products=False,
    )

    assert key == "despesas-cc-ranking-v1|fornecedores|20250601|20250630|02|0101|25|0"
