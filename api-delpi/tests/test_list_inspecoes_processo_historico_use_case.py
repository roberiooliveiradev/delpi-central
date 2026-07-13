from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case import (
    ListInspecoesProcessoHistoricoUseCase,
    historico_lookback_floor,
)


def test_list_inspecoes_processo_historico_normalizes_and_pages() -> None:
    repository = MagicMock()
    repository.list_historico_by_branch.return_value = [
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Ordem_Producao": "10565201002",
            "Codigo_Produto": "50233817",
            "Descricao_Produto": "CB18BRAN-00332/06/06-0000-6345",
            "Revisao_Produto": "00",
            "Quantidade_OP": 4.05,
            "Chave_Cabecalho_Inspecao": "00059332",
            "Origem_Inspecao": "MATA650",
            "Qtde_Ensaios": 12,
            "Qtde_Ensaios_Aprovados": 12,
            "Qtde_Ensaios_Reprovados": 0,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_Operacoes": 1,
            "Qtde_Ensaiadores": 1,
            "Resultado_Inspecao_Codigo": "A",
            "Resultado_Inspecao": "APROVADO",
            "Primeira_Data_Medicao_Date": date(2026, 7, 12),
            "Ultima_Data_Medicao_Date": date(2026, 7, 12),
            "Ultima_Hora_Medicao": "09:16",
            "Matricula_Ultimo_Ensaiador": "20266",
            "Nome_Ultimo_Ensaiador": "MAIANA SANTOS DE JESUS",
        },
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Ordem_Producao": "10565201001",
            "Codigo_Produto": "50233816",
            "Descricao_Produto": "OUTRO",
            "Revisao_Produto": "00",
            "Quantidade_OP": 1.0,
            "Chave_Cabecalho_Inspecao": "00059331",
            "Origem_Inspecao": "MATA650",
            "Qtde_Ensaios": 1,
            "Qtde_Ensaios_Aprovados": 0,
            "Qtde_Ensaios_Reprovados": 1,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_Operacoes": 1,
            "Qtde_Ensaiadores": 1,
            "Resultado_Inspecao_Codigo": "R",
            "Resultado_Inspecao": "REPROVADO",
            "Primeira_Data_Medicao_Date": date(2026, 7, 11),
            "Ultima_Data_Medicao_Date": date(2026, 7, 11),
            "Ultima_Hora_Medicao": "08:00",
            "Matricula_Ultimo_Ensaiador": "1",
            "Nome_Ultimo_Ensaiador": "TESTE",
        },
    ]

    use_case = ListInspecoesProcessoHistoricoUseCase(repository)
    with patch(
        "app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case.historico_lookback_floor",
        return_value="2025-07-13",
    ):
        result = use_case.execute(
            branch="02", page=1, page_size=1, codigo_produto="50233817"
        )

    repository.list_historico_by_branch.assert_called_once_with(
        "02",
        offset=0,
        fetch_next=2,
        ordem_producao=None,
        codigo_produto="50233817",
        resultado=None,
        data_inicio="2025-07-13",
        data_fim=None,
    )
    payload = result.to_dict()
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["has_next"] is True
    assert len(payload["items"]) == 1
    assert payload["items"][0]["ordem_producao"] == "10565201002"


def test_list_inspecoes_processo_historico_clamps_page_size_and_filters() -> None:
    repository = MagicMock()
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesProcessoHistoricoUseCase(repository)
    with patch(
        "app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case.historico_lookback_floor",
        return_value="2025-07-13",
    ):
        result = use_case.execute(
            branch="01",
            page=2,
            page_size=999,
            ordem_producao="10565201002",
            codigo_produto="50233817",
            resultado="a",
            data_inicio="2026-01-01",
            data_fim="2026-07-12",
        )

    repository.list_historico_by_branch.assert_called_once_with(
        "01",
        offset=50,
        fetch_next=51,
        ordem_producao="10565201002",
        codigo_produto="50233817",
        resultado="A",
        data_inicio="2026-01-01",
        data_fim="2026-07-12",
    )
    assert result.has_next is False
    assert result.items == []


def test_list_inspecoes_processo_historico_raises_floor_when_inicio_too_old() -> None:
    repository = MagicMock()
    repository.list_historico_by_branch.return_value = []
    use_case = ListInspecoesProcessoHistoricoUseCase(repository)

    with patch(
        "app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case.historico_lookback_floor",
        return_value="2025-07-13",
    ):
        use_case.execute(
            branch="01",
            codigo_produto="50233817",
            data_inicio="2020-01-01",
        )

    repository.list_historico_by_branch.assert_called_once()
    assert repository.list_historico_by_branch.call_args.kwargs["data_inicio"] == (
        "2025-07-13"
    )


def test_historico_lookback_floor_handles_month_end() -> None:
    assert historico_lookback_floor(date(2026, 3, 31)) == "2025-03-31"


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_processo_historico_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.list_historico_by_branch.assert_not_called()


def test_list_inspecoes_processo_historico_rejects_invalid_resultado() -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="resultado inválido"):
        use_case.execute(branch="01", resultado="X", codigo_produto="90263652")

    repository.list_historico_by_branch.assert_not_called()


def test_list_inspecoes_processo_historico_requires_selective_filter() -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="ordem de produção ou código de produto"):
        use_case.execute(branch="01", data_inicio="2026-01-01", data_fim="2026-07-13")

    repository.list_historico_by_branch.assert_not_called()


def test_list_inspecoes_processo_historico_rejects_inverted_dates() -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="data_inicio"):
        use_case.execute(
            branch="01",
            codigo_produto="50233817",
            data_inicio="2026-07-12",
            data_fim="2026-01-01",
        )

    repository.list_historico_by_branch.assert_not_called()
