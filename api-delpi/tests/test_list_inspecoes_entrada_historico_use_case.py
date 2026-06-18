from unittest.mock import MagicMock

import pytest

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
    InspecoesEntradaHistoricoFilters,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_historico_use_case import (
    ListInspecoesEntradaHistoricoUseCase,
)


def _sample_row() -> dict:
    return {
        "Filial": "01",
        "Id_Inspecao": "01|000042999|2|0002|000532|01|10110388|AUTO000952",
        "Data_Recebimento": "20260611",
        "Hora_Recebimento": "09:39",
        "Data_Laudo": "2026-06-11",
        "Hora_Laudo": "10:06",
        "Nota_Fiscal": "000042999",
        "Serie_Nota_Fiscal": "2",
        "Item_Nota_Fiscal": "0002",
        "Codigo_Fornecedor": "000532",
        "Loja_Fornecedor": "01",
        "Nome_Fornecedor": "MULTIPRINT ETIQUETAS LTDA",
        "Codigo_Produto": "10110388",
        "Lote": "AUTO000952",
        "Lote_Fornecedor": "",
        "Quantidade": 3000,
        "Unidade_Medida": "PC",
        "Codigo_Situacao": "3",
        "Status_Inspecao": "REJEITADA",
        "Resultado_Resumo": "REJEITADA",
        "Codigo_Laudo": "E",
        "Quantidade_Aprovada": None,
        "Quantidade_Rejeitada": 3000,
        "Justificativa_Laudo": "",
        "Matricula_Ensaiador": "30006",
        "Nome_Ensaiador": "NATHALIA FERNANDES SALES",
        "Login_Ensaiador": "NATHALIA",
        "Qtde_Ensaios": 6,
        "Qtde_Ensaios_Reprovados": 1,
        "Eh_Aprovada": 0,
        "Eh_Rejeitada": 1,
    }


def test_list_inspecoes_entrada_historico_normalizes_items_and_pagination() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 731
    repository.list_historico_by_branch.return_value = [_sample_row()]

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    result = use_case.execute(branch="01", page=1, page_size=50)

    expected_filters = InspecoesEntradaHistoricoFilters()
    repository.count_historico_by_branch.assert_called_once_with("01", expected_filters)
    repository.list_historico_by_branch.assert_called_once_with(
        "01",
        page=1,
        page_size=50,
        filters=expected_filters,
    )

    payload = result.to_dict()
    assert payload["branch"] == "01"
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["inspection_id"] == "01|000042999|2|0002|000532|01|10110388|AUTO000952"
    assert item["report_date"] == "2026-06-11"
    assert item["invoice_number"] == "000042999"
    assert item["inspector_registration"] == "30006"
    assert item["approved_quantity"] is None
    assert item["rejected_quantity"] == 3000.0
    assert item["is_approved"] is False
    assert item["is_rejected"] is True
    assert payload["pagination"] == {
        "page": 1,
        "page_size": 50,
        "total": 731,
        "total_pages": 15,
    }
    assert payload["filters"] == {
        "result": None,
        "date_from": None,
        "date_to": None,
        "supplier": None,
        "product_code": None,
        "inspector": None,
        "invoice_number": None,
        "lot": None,
    }


def test_list_inspecoes_entrada_historico_applies_result_filter() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 1
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    use_case.execute(branch="01", result="APROVADA")

    filters = repository.count_historico_by_branch.call_args.args[1]
    assert filters.result == "APROVADA"


def test_list_inspecoes_entrada_historico_applies_date_filters() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 0
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    use_case.execute(
        branch="02",
        date_from="2026-01-01",
        date_to="2026-06-30",
    )

    filters = repository.count_historico_by_branch.call_args.args[1]
    assert filters.date_from == "2026-01-01"
    assert filters.date_to == "2026-06-30"


def test_list_inspecoes_entrada_historico_applies_invoice_number_filter() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 1
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    use_case.execute(branch="01", invoice_number="000042999")

    filters = repository.count_historico_by_branch.call_args.args[1]
    assert filters.invoice_number == "000042999"


def test_list_inspecoes_entrada_historico_returns_empty_list_when_no_rows() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 0
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    result = use_case.execute(branch="02", page=1, page_size=50)

    payload = result.to_dict()
    assert payload["items"] == []
    assert payload["pagination"]["total"] == 0
    assert payload["pagination"]["total_pages"] == 1


def test_list_inspecoes_entrada_historico_clamps_page_size() -> None:
    repository = MagicMock()
    repository.count_historico_by_branch.return_value = 0
    repository.list_historico_by_branch.return_value = []

    use_case = ListInspecoesEntradaHistoricoUseCase(repository)
    use_case.execute(branch="01", page=0, page_size=500)

    repository.list_historico_by_branch.assert_called_once()
    call_kwargs = repository.list_historico_by_branch.call_args.kwargs
    assert call_kwargs["page"] == 1
    assert call_kwargs["page_size"] == 200


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_entrada_historico_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.count_historico_by_branch.assert_not_called()
    repository.list_historico_by_branch.assert_not_called()


def test_list_inspecoes_entrada_historico_rejects_invalid_result() -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="result inválido"):
        use_case.execute(branch="01", result="INVALIDO")

    repository.count_historico_by_branch.assert_not_called()


def test_list_inspecoes_entrada_historico_rejects_date_from_after_date_to() -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="date_from deve ser menor ou igual a date_to"):
        use_case.execute(
            branch="01",
            date_from="2026-06-30",
            date_to="2026-01-01",
        )

    repository.count_historico_by_branch.assert_not_called()


def test_list_inspecoes_entrada_historico_rejects_invalid_date_format() -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaHistoricoUseCase(repository)

    with pytest.raises(ValueError, match="date_from inválida"):
        use_case.execute(branch="01", date_from="31-06-2026")

    repository.count_historico_by_branch.assert_not_called()
