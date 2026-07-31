"""Use case — detalhes de retrabalho (envelope paged_list + aliases EN)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.retrabalho.retrabalho_detalhes_request import RetrabalhoDetalhesRequest
from app.application.use_cases.retrabalho.get_retrabalho_detalhes_use_case import (
    GetRetrabalhoDetalhesUseCase,
)


def test_detalhes_envelope_has_pagination_is_complete_and_en_aliases() -> None:
    repo = MagicMock()
    repo.count_detalhes.return_value = 1
    repo.get_detalhes.return_value = [
        {
            "data_referencia": "2026-07-15",
            "filial": "01",
            "op": "OP1",
            "produto": "P1",
            "operacao": "10",
            "recurso": "R1",
            "centro_custo": "CC1",
            "codigo_operador": "100",
            "nome_operador": "Ana",
            "tempo_horas": 1.5,
            "valor_parada": 10.0,
            "fonte_custo": "SB2",
            "motivo": "Retrabalho",
            "observacao": "ok",
            "recno": 42,
        }
    ]
    use_case = GetRetrabalhoDetalhesUseCase(repo)
    request = RetrabalhoDetalhesRequest.from_query(
        filial="01",
        data_inicio="2026-07-01",
        data_fim="2026-07-31",
        page=1,
        page_size=25,
    )

    result = use_case.execute(request)

    item = result["items"][0]
    assert item["hours"] == item["tempoHoras"] == 1.5
    assert item["branch"] == item["filial"] == "01"
    assert item["reference_date"] == item["dataReferencia"]
    assert item["cost_center"] == item["centroCusto"] == "CC1"
    assert result["pagination"]["is_complete"] is True
    assert result["pageSize"] == result["page_size"] == 25
    assert result["totalPages"] == result["total_pages"]
