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
    # Média por instância: o ranking soma o grão já mediado (proc_lvl), não a tabela crua.
    assert "SUM(pl.economia_bruta)" in source
    assert "AS economia_diaria" in source
    assert "horas_diaria" in source
    assert "/ 30.0" not in source
    assert "ORDER BY economia_diaria DESC" in source


def test_instance_average_cte_does_two_level_aggregation():
    """Regra jul/2026: soma revisões por instância e soma entre instâncias."""
    from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
        _instance_average_cte,
    )

    cte = _instance_average_cte("d.cenario_tipo IN ('melhoria')")
    # Nível 1 (instância): soma revisões por instância.
    assert "SUM(COALESCE(d.economia_bruta, 0))" in cte
    assert "GROUP BY d.processo_id, d.competencia" in cte
    # Nível 2 (processo): soma entre instâncias ativas.
    assert "SUM(economia_bruta)" in cte
    assert "COUNT(*) AS instancias_ativas" in cte
