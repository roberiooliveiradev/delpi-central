from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.application.dto.financeiro_inadimplencia.clientes_request import (
    InadimplenciaClientesRequest,
)
from app.application.dto.financeiro_inadimplencia.titulos_request import (
    InadimplenciaTitulosRequest,
)
from app.application.use_cases.financeiro_inadimplencia.get_clientes_use_case import (
    GetInadimplenciaClientesUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_titulos_use_case import (
    GetInadimplenciaTitulosUseCase,
)


def test_clientes_use_case_pagination_total_is_customers_not_titles() -> None:
    repository = MagicMock()
    repository.count_clientes.return_value = 42
    repository.list_clientes.return_value = [
        {
            "cliente_codigo": "000001",
            "loja": "09",
            "nome_cliente": "WEG",
            "nome_reduzido": "WEG",
            "total_titulos": 1999,
            "titulos_em_dia": 1884,
            "titulos_atraso": 115,
            "valor_total": 100.0,
            "valor_atraso": 10.0,
            "percentual_em_dia_qtd": 94.25,
            "percentual_em_dia_valor": 91.05,
        }
    ]
    use_case = GetInadimplenciaClientesUseCase(repository=repository)
    request = InadimplenciaClientesRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        page=1,
        page_size=20,
    )

    result = use_case.execute(request)
    assert result.pagination.total_items == 42
    assert result.pagination.total_pages == 3
    assert len(result.items) == 1
    repository.count_clientes.assert_called_once()


def test_titulos_use_case_maps_faixa_and_dates() -> None:
    repository = MagicMock()
    repository.count_titulos.return_value = 1
    repository.list_titulos.return_value = [
        {
            "filial": "",
            "prefixo": "02",
            "numero": "014413",
            "parcela": "",
            "tipo": "NF",
            "cliente_codigo": "000001",
            "loja": "09",
            "nome_cliente": "WEG LINHARES",
            "nome_reduzido": "WEG",
            "data_emissao": date(2026, 2, 5),
            "data_vencimento_real": date(2026, 2, 26),
            "data_baixa": date(2026, 6, 26),
            "valor_titulo": 467511.69,
            "pago_em_dia": 0,
            "dias_atraso": 120,
            "faixa_atraso": "ATRASO_ACIMA_30_DIAS",
        }
    ]
    use_case = GetInadimplenciaTitulosUseCase(repository=repository)
    request = InadimplenciaTitulosRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        customer_code="000001",
        store_code="09",
        status="late",
    )

    result = use_case.execute(request)
    item = result.items[0]
    assert item.data_emissao == "2026-02-05"
    assert item.pago_em_dia is False
    assert item.faixa_atraso["codigo"] == "ATRASO_ACIMA_30_DIAS"
    assert item.faixa_atraso["rotulo"] == "Acima de 30 dias"
    assert result.pagination.total_items == 1
