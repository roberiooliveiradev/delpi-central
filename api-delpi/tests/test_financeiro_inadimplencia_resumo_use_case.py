from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)
from app.application.use_cases.financeiro_inadimplencia.get_faixas_atraso_use_case import (
    GetInadimplenciaFaixasAtrasoUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_resumo_use_case import (
    GetInadimplenciaResumoUseCase,
)


def test_resumo_use_case_calculates_indicators_and_complements() -> None:
    repository = MagicMock()
    repository.get_resumo.return_value = {
        "titulos": 100,
        "titulos_em_dia": 92,
        "titulos_atraso": 8,
        "valor_total": 1000.0,
        "valor_em_dia": 900.0,
        "valor_atraso": 100.0,
    }
    use_case = GetInadimplenciaResumoUseCase(repository=repository)
    request = InadimplenciaQueryRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
    )

    result = use_case.execute(request)
    assert result.totais["titulos"] == 100
    assert result.indicadores["percentual_em_dia_qtd"] == 92.0
    assert result.indicadores["percentual_inadimplencia_qtd"] == 8.0
    assert result.indicadores["percentual_em_dia_valor"] == 90.0
    assert result.indicadores["percentual_inadimplencia_valor"] == 10.0


def test_resumo_use_case_handles_empty_dataset_without_nan() -> None:
    repository = MagicMock()
    repository.get_resumo.return_value = {
        "titulos": 0,
        "titulos_em_dia": 0,
        "titulos_atraso": 0,
        "valor_total": 0,
        "valor_em_dia": 0,
        "valor_atraso": 0,
    }
    use_case = GetInadimplenciaResumoUseCase(repository=repository)
    request = InadimplenciaQueryRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
    )

    result = use_case.execute(request)
    assert result.indicadores["percentual_em_dia_qtd"] == 0.0
    assert result.indicadores["percentual_inadimplencia_qtd"] == 0.0
    assert result.indicadores["percentual_em_dia_valor"] == 0.0
    assert result.indicadores["percentual_inadimplencia_valor"] == 0.0


def test_faixas_use_case_returns_official_order_and_fills_missing() -> None:
    repository = MagicMock()
    repository.get_faixas_atraso.return_value = [
        {"codigo": "ATRASO_1_A_5_DIAS", "quantidade": 10, "valor": 100.0},
        {"codigo": "EM_DIA", "quantidade": 90, "valor": 900.0},
    ]
    use_case = GetInadimplenciaFaixasAtrasoUseCase(repository=repository)
    request = InadimplenciaQueryRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
    )

    result = use_case.execute(request)
    codes = [item.codigo for item in result.items]
    assert codes == [
        "EM_DIA",
        "ATRASO_1_A_5_DIAS",
        "ATRASO_6_A_15_DIAS",
        "ATRASO_16_A_30_DIAS",
        "ATRASO_ACIMA_30_DIAS",
    ]
    assert result.items[0].quantidade == 90
    assert result.items[2].quantidade == 0
    assert result.items[0].ordem == 1
