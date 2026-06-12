from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from tm_app.application.services.instancia_duplicate_service import (
    InstanciaDuplicateService,
    InstanciaNotFoundError,
)


@patch("tm_app.application.services.instancia_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.instancia_duplicate_service.VinculoRepository")
@patch("tm_app.application.services.instancia_duplicate_service.InvestimentoRepository")
@patch("tm_app.application.services.instancia_duplicate_service.MedicaoRepository")
@patch("tm_app.application.services.instancia_duplicate_service.RevisaoRepository")
@patch("tm_app.application.services.instancia_duplicate_service.ProcessoInstanciaRepository")
def test_duplicate_instancia_copies_timeline_to_new_par(
    mock_inst_cls,
    mock_rev_cls,
    mock_med_cls,
    mock_inv_cls,
    mock_vin_cls,
    mock_conn_factory,
):
    conn = MagicMock()
    mock_conn_factory.return_value = conn

    inst_repo = mock_inst_cls.return_value
    rev_repo = mock_rev_cls.return_value
    med_repo = mock_med_cls.return_value
    inv_repo = mock_inv_cls.return_value
    vin_repo = mock_vin_cls.return_value

    inst_repo.get.return_value = {
        "instancia_id": "i-src",
        "processo_id": "p1",
        "codigo_filial": "01",
        "codigo_setor": "engenharia",
    }
    rev_repo.list_by_instancia.side_effect = lambda iid: (
        [
            {
                "revisao_id": "r-old",
                "versao_revisao": "1.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2024-01-01",
            }
        ]
        if iid == "i-src"
        else []
    )
    inst_repo.create.return_value = {
        "instancia_id": "i-dst",
        "processo_id": "p1",
        "codigo_filial": "02",
        "codigo_setor": "producao",
    }
    rev_repo.create.return_value = {"revisao_id": "r-new"}
    med_repo.get_by_revisao.return_value = None
    inv_repo.list_by_revisao.return_value = []
    vin_repo.list_by_revisao.return_value = []

    result = InstanciaDuplicateService().duplicate(
        "i-src",
        filial_id="02",
        setor_id="producao",
    )

    assert result["instancia"]["instancia_id"] == "i-dst"
    assert result["processo_id"] == "p1"
    assert result["copiados"]["revisoes"] == 1
    conn.commit.assert_called_once()
    inst_repo.create.assert_called_once()
    rev_repo.create.assert_called_once()
    create_payload = rev_repo.create.call_args[0][0]
    assert create_payload["instancia_id"] == "i-dst"
    assert create_payload["processo_id"] == "p1"


@patch("tm_app.application.services.instancia_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.instancia_duplicate_service.ProcessoInstanciaRepository")
def test_duplicate_instancia_rejects_same_par(mock_inst_cls, mock_conn_factory):
    mock_conn_factory.return_value = MagicMock()
    mock_inst_cls.return_value.get.return_value = {
        "instancia_id": "i-src",
        "processo_id": "p1",
        "codigo_filial": "01",
        "codigo_setor": "engenharia",
    }

    with pytest.raises(ValueError, match="Destino igual"):
        InstanciaDuplicateService().duplicate(
            "i-src",
            filial_id="01",
            setor_id="engenharia",
        )


@patch("tm_app.application.services.instancia_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.instancia_duplicate_service.ProcessoInstanciaRepository")
def test_duplicate_instancia_not_found(mock_inst_cls, mock_conn_factory):
    mock_conn_factory.return_value = MagicMock()
    mock_inst_cls.return_value.get.return_value = None

    with pytest.raises(InstanciaNotFoundError):
        InstanciaDuplicateService().duplicate(
            "missing",
            filial_id="02",
            setor_id="producao",
        )
