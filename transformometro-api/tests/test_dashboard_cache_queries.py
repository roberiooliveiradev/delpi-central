"""Valida expressões SQL do cache dashboard_calculos (playbook 5.4)."""

from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
    _INVESTIMENTO_TOTAL_SQL,
)


def test_investimento_total_sql_includes_all_components():
    assert "investimento_unico_mes" in _INVESTIMENTO_TOTAL_SQL
    assert "custo_recorrente_mes" in _INVESTIMENTO_TOTAL_SQL
    assert "custo_recursos_compartilhados_mes" in _INVESTIMENTO_TOTAL_SQL


def test_ranking_query_orders_by_economia_diaria_from_bruta():
    import inspect

    source = inspect.getsource(DashboardCalculoRepository.query_ranking_processos)
    assert "SUM(d.economia_bruta) / 30.0 AS economia_diaria" in source
    assert "ORDER BY economia_diaria DESC" in source
