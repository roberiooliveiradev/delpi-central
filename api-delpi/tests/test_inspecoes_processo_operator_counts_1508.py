"""Regressão #1508: total de sessões inspecionadas por operador e OP."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.inspecoes_processo.get_inspecoes_processo_historico_detalhe_use_case import (
    GetInspecoesProcessoHistoricoDetalheUseCase,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    InspecoesProcessoRepository,
)


def test_operator_count_is_complete_even_if_measurements_are_paginated() -> None:
    repository = MagicMock()
    repository.get_historico_cabecalho_by_op.return_value = {
        "Filial": "02",
        "Ordem_Producao": "10565201002",
    }
    # A página de medições possui apenas uma linha, apesar de haver várias sessões.
    repository.list_historico_detalhe_itens_by_op.return_value = [
        {"Filial": "02", "Ordem_Producao": "10565201002", "Codigo_Ensaio": "20"},
        {"Filial": "02", "Ordem_Producao": "10565201002", "Codigo_Ensaio": "21"},
    ]
    repository.list_historico_inspecoes_por_operador_by_op.return_value = [
        {"Matricula_Ensaiador": " 20266 ", "Nome_Ensaiador": " MAIANA ", "Qtde_Inspecoes": 3},
        {"Matricula_Ensaiador": " 20145 ", "Nome_Ensaiador": " CARLA ", "Qtde_Inspecoes": 1},
    ]

    result = GetInspecoesProcessoHistoricoDetalheUseCase(repository).execute(
        branch="02", ordem_producao="10565201002", page=1, page_size=1
    )

    assert result is not None
    payload = result.to_dict()
    assert payload["has_next"] is True
    assert len(payload["items"]) == 1
    assert [(item["matricula_ensaiador"], item["qtde_inspecoes"])
            for item in payload["inspecoes_por_operador"]] == [
        ("20266", 3), ("20145", 1),
    ]
    assert payload["inspecoes_por_operador"][0]["inspection_count"] == 3
    repository.list_historico_inspecoes_por_operador_by_op.assert_called_once_with(
        "02", ordem_producao="10565201002"
    )


def test_operator_count_is_not_queried_for_missing_op() -> None:
    repository = MagicMock()
    repository.get_historico_cabecalho_by_op.return_value = None
    result = GetInspecoesProcessoHistoricoDetalheUseCase(repository).execute(
        branch="01", ordem_producao="NAOEXISTE"
    )
    assert result is None
    repository.list_historico_inspecoes_por_operador_by_op.assert_not_called()


def test_operator_count_query_groups_sessions_not_assay_rows() -> None:
    # Contrato SQL: uma sessão = matrícula + operação + data + hora.
    import inspect

    source = inspect.getsource(
        InspecoesProcessoRepository.list_historico_inspecoes_por_operador_by_op
    )
    assert "HISTORICO_TELA_VIEW" in source
    assert "GROUP BY Matricula_Ensaiador, Operacao, Data_Medicao_Date, Hora_Medicao" in source
    assert "GROUP BY Sessoes.Matricula_Ensaiador" in source
    assert "COUNT_BIG(*) AS Qtde_Inspecoes" in source
    assert '_where_branch("Filial", branch)' in source
    assert "Ordem_Producao LIKE ?" in source
    assert "QPR_RECNO" not in source
