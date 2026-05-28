from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.processo_duplicate_service import (
    ProcessoDuplicateService,
    ProcessoNotFoundError,
)


@patch("tm_app.application.services.processo_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.processo_duplicate_service.VinculoRepository")
@patch("tm_app.application.services.processo_duplicate_service.InvestimentoRepository")
@patch("tm_app.application.services.processo_duplicate_service.MedicaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.RevisaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoRepository")
def test_duplicate_copies_process_tree(
    mock_proc_cls,
    mock_rev_cls,
    mock_med_cls,
    mock_inv_cls,
    mock_vin_cls,
    mock_conn_factory,
):
    conn = MagicMock()
    mock_conn_factory.return_value = conn

    proc_repo = mock_proc_cls.return_value
    rev_repo = mock_rev_cls.return_value
    med_repo = mock_med_cls.return_value
    inv_repo = mock_inv_cls.return_value
    vin_repo = mock_vin_cls.return_value

    proc_repo.get.return_value = {
        "processo_id": "p-old",
        "nome_processo": "Processo A",
        "filial_id": "01",
        "setor_id": "engenharia",
        "status_processo": "ativo",
    }
    proc_repo.create.return_value = {
        "processo_id": "p-new",
        "codigo_processo": "PROC-0099",
        "nome_processo": "Processo A (cópia)",
    }
    rev_repo.list_by_processo.return_value = [
        {
            "revisao_id": "r-old",
            "versao_revisao": "1.0",
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2024-01-01",
        },
    ]
    rev_repo.create.return_value = {"revisao_id": "r-new"}
    med_repo.get_by_revisao.return_value = {"volume_mensal": 10}
    inv_repo.list_by_revisao.return_value = [
        {"tipo_investimento": "unico", "descricao_item": "Licença", "quantidade": 1, "valor_unitario": 100}
    ]
    vin_repo.list_by_revisao.return_value = [
        {
            "recurso_compartilhado_id": "rc-1",
            "ativo": True,
        }
    ]

    result = ProcessoDuplicateService().duplicate("p-old")

    assert result["processo"]["processo_id"] == "p-new"
    assert result["copiados"]["revisoes"] == 1
    assert result["copiados"]["medicoes"] == 1
    assert result["copiados"]["investimentos"] == 1
    assert result["copiados"]["vinculos"] == 1
    conn.commit.assert_called_once()
    proc_repo.create.assert_called_once()
    rev_repo.create.assert_called_once()
    med_repo.create.assert_called_once()
    inv_repo.create.assert_called_once()
    vin_repo.create.assert_called_once()


@patch("tm_app.application.services.processo_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoRepository")
def test_duplicate_raises_when_process_missing(mock_proc_cls, mock_conn_factory):
    mock_conn_factory.return_value = MagicMock()
    mock_proc_cls.return_value.get.return_value = None

    try:
        ProcessoDuplicateService().duplicate("missing")
        assert False, "expected ProcessoNotFoundError"
    except ProcessoNotFoundError:
        pass
