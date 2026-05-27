from __future__ import annotations

from datetime import date

from tm_app.domain.services.recurso_custo_resolver import resolve_recurso_valor_mensal


def test_resolve_uses_historical_value_for_month():
    resource = {
        "recurso_compartilhado_id": "r1",
        "valor_total_recorrente": 999,
    }
    custos = [
        {
            "recurso_compartilhado_id": "r1",
            "valor_mensal": 100,
            "data_inicio_vigencia": "2024-01-01",
            "data_fim_vigencia": "2024-06-30",
            "deletado": False,
        },
        {
            "recurso_compartilhado_id": "r1",
            "valor_mensal": 150,
            "data_inicio_vigencia": "2024-07-01",
            "data_fim_vigencia": None,
            "deletado": False,
        },
    ]

    assert resolve_recurso_valor_mensal(resource, custos, date(2024, 3, 15)) == 100.0
    assert resolve_recurso_valor_mensal(resource, custos, date(2024, 8, 1)) == 150.0


def test_resolve_falls_back_to_catalog_value_without_history():
    resource = {"recurso_compartilhado_id": "r1", "valor_total_recorrente": 42}
    assert resolve_recurso_valor_mensal(resource, [], date(2025, 1, 1)) == 42.0
