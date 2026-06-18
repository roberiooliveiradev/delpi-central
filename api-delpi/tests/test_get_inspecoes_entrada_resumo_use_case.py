from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.get_inspecoes_entrada_resumo_use_case import (
    GetInspecoesEntradaResumoUseCase,
)


def test_get_inspecoes_entrada_resumo_normalizes_row() -> None:
    repository = MagicMock()
    repository.get_resumo_by_branch.return_value = {
        "Filial": "01",
        "Inspecoes_Pendentes": 6,
        "Ja_Inspecionados": 731,
        "Inspecoes_Aprovadas": 730,
        "Inspecoes_Rejeitadas": 1,
        "Taxa_Aprovacao": 99.86,
        "Qtde_Inspecoes_Com_Tempo": 728,
        "Tempo_Medio_Horas": 16.46,
        "Tempo_Medio_Dias": 0.69,
    }

    use_case = GetInspecoesEntradaResumoUseCase(repository)
    result = use_case.execute(branch="01")

    repository.get_resumo_by_branch.assert_called_once_with("01")
    payload = result.to_dict()
    assert payload == {
        "branch": "01",
        "pending_inspections": 6,
        "inspected": 731,
        "approved_inspections": 730,
        "rejected_inspections": 1,
        "approval_rate": 99.86,
        "inspections_with_time": 728,
        "average_time_hours": 16.46,
        "average_time_days": 0.69,
    }


def test_get_inspecoes_entrada_resumo_returns_zeros_when_row_missing() -> None:
    repository = MagicMock()
    repository.get_resumo_by_branch.return_value = None

    use_case = GetInspecoesEntradaResumoUseCase(repository)
    result = use_case.execute(branch="02")

    assert result.to_dict() == {
        "branch": "02",
        "pending_inspections": 0,
        "inspected": 0,
        "approved_inspections": 0,
        "rejected_inspections": 0,
        "approval_rate": 0.0,
        "inspections_with_time": 0,
        "average_time_hours": 0.0,
        "average_time_days": 0.0,
    }


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_get_inspecoes_entrada_resumo_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = GetInspecoesEntradaResumoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.get_resumo_by_branch.assert_not_called()
