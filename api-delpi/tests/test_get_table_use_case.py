"""GetTableUseCase normaliza lista do repositório para dict scalar."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.system.system_requests import GetTableRequest
from app.application.use_cases.system.get_table_use_case import GetTableUseCase


def test_get_table_use_case_returns_first_dict_from_list():
    repository = MagicMock()
    repository.get_table.return_value = [
        {"X2_CHAVE": "SB1", "X2_NOME": "Produtos"},
        {"X2_CHAVE": "SB2"},
    ]
    use_case = GetTableUseCase(repository)

    result = use_case.execute(GetTableRequest(table_name="SB1010"))

    assert isinstance(result, dict)
    assert result["X2_CHAVE"] == "SB1"


def test_get_table_use_case_passes_through_dict():
    repository = MagicMock()
    repository.get_table.return_value = {"name": "SB1010"}
    use_case = GetTableUseCase(repository)

    result = use_case.execute(GetTableRequest(table_name="SB1010"))

    assert result == {"name": "SB1010"}
