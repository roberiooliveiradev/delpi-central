import inspect

from app.infrastructure.persistence.totvs.production_repositories.production_orders_repository import (
    ProductionOrdersRepository,
)


def test_allocation_gaps_sql_uses_component_code_and_filial_joins() -> None:
    """Regressão: D4_COD (componente) + JOIN por filial — evita timeout e produto errado."""
    src = inspect.getsource(ProductionOrdersRepository.fetch_allocation_gaps)
    assert "RE.D4_COD AS component_code" in src
    assert "RE.D4_PRODUTO AS component_code" not in src
    assert "P.B1_COD = RE.D4_COD" in src
    assert "OP.C2_FILIAL = RE.D4_FILIAL" in src
    assert "OA.H8_FILIAL = RE.D4_FILIAL" in src
    assert "WITH (NOLOCK)" in src


def test_open_and_finished_orders_sql_join_by_filial() -> None:
    open_src = inspect.getsource(ProductionOrdersRepository.fetch_open_orders)
    finished_src = inspect.getsource(ProductionOrdersRepository.fetch_finished_orders)
    for src in (open_src, finished_src):
        assert "RE.D4_FILIAL = OP.C2_FILIAL" in src
        assert "OA.H8_FILIAL = OP.C2_FILIAL" in src
