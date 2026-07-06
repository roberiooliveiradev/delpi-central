from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.processo_duplicate_service import (
    ProcessoDuplicateService,
    ProcessoNotFoundError,
)


@patch("tm_app.application.services.processo_duplicate_service.RevisaoEvidenceStorage")
@patch("tm_app.application.services.processo_duplicate_service.RevisaoEvidenceRepository")
@patch("tm_app.application.services.processo_duplicate_service.RevisaoDecomposicaoOverlayRepository")
@patch("tm_app.application.services.processo_duplicate_service.RevisaoDiagramOverlayRepository")
@patch("tm_app.application.services.processo_duplicate_service.InstanciaDecomposicaoEscopoRepository")
@patch("tm_app.application.services.processo_duplicate_service.InstanciaDiagramEscopoRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoDecomposicaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoDiagramRepository")
@patch("tm_app.application.services.processo_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoInstanciaRepository")
@patch("tm_app.application.services.processo_duplicate_service.VinculoRepository")
@patch("tm_app.application.services.processo_duplicate_service.InvestimentoRepository")
@patch("tm_app.application.services.processo_duplicate_service.MedicaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.RevisaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoRepository")
def test_duplicate_copies_full_process_tree(
    mock_proc_cls,
    mock_rev_cls,
    mock_med_cls,
    mock_inv_cls,
    mock_vin_cls,
    mock_inst_cls,
    mock_conn_factory,
    mock_diagram_cls,
    mock_decomp_cls,
    mock_inst_diagram_cls,
    mock_inst_decomp_cls,
    mock_rev_diagram_cls,
    mock_rev_decomp_cls,
    mock_evidence_cls,
    mock_storage_cls,
):
    conn = MagicMock()
    mock_conn_factory.return_value = conn

    proc_repo = mock_proc_cls.return_value
    rev_repo = mock_rev_cls.return_value
    med_repo = mock_med_cls.return_value
    inv_repo = mock_inv_cls.return_value
    vin_repo = mock_vin_cls.return_value
    inst_repo = mock_inst_cls.return_value
    diagram_repo = mock_diagram_cls.return_value
    decomp_repo = mock_decomp_cls.return_value
    inst_diagram_repo = mock_inst_diagram_cls.return_value
    inst_decomp_repo = mock_inst_decomp_cls.return_value
    rev_diagram_repo = mock_rev_diagram_cls.return_value
    rev_decomp_repo = mock_rev_decomp_cls.return_value
    evidence_repo = mock_evidence_cls.return_value
    evidence_storage = mock_storage_cls.return_value

    proc_repo.get.return_value = {
        "processo_id": "p-old",
        "nome_processo": "Processo A",
        "status_processo": "ativo",
    }
    inst_repo.list_by_processo.return_value = [
        {
            "instancia_id": "i-source",
            "codigo_filial": "01",
            "todas_filiais_ativas": False,
            "setores": [{"codigo_setor": "engenharia"}],
            "contexto": {"schema": "instancia_contexto_v1"},
        }
    ]
    inst_repo.create.return_value = {"instancia_id": "i-new"}
    proc_repo.create.return_value = {
        "processo_id": "p-new",
        "codigo_processo": "PROC-0099",
        "nome_processo": "Processo A (cópia)",
    }
    diagram_repo.get.return_value = {"conteudo": {"nodes": []}, "mermaid_cached": "graph TD"}
    decomp_repo.get.return_value = {"conteudo": {"nodes": []}}
    inst_diagram_repo.get.return_value = {
        "node_ids": ["n1"],
        "inherit_all": False,
        "include_boundary_edges": True,
    }
    inst_decomp_repo.get.return_value = {
        "node_ids": ["pk1"],
        "inherit_all": False,
        "include_descendants": True,
    }
    rev_repo.list_by_instancia.return_value = [
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
        {
            "tipo_investimento": "unico",
            "descricao_item": "Licença",
            "quantidade": 1,
            "valor_unitario": 100,
        }
    ]
    vin_repo.list_by_revisao.return_value = [
        {
            "recurso_compartilhado_id": "rc-1",
            "ativo": True,
        }
    ]
    rev_diagram_repo.get.return_value = {"conteudo": {"node_overrides": {}}, "mermaid_cached": None}
    rev_decomp_repo.get.return_value = {"conteudo": {"node_overrides": {}}}
    evidence_repo.list_by_revisao.return_value = [
        {
            "tipo": "anexo",
            "nome_arquivo": "evidencia.pdf",
            "nome_armazenado": "abc.pdf",
            "tipo_mime": "application/pdf",
            "tamanho_bytes": 100,
        }
    ]
    evidence_storage.copy_file.return_value = "def.pdf"

    result = ProcessoDuplicateService().duplicate("p-old")

    assert result["processo"]["processo_id"] == "p-new"
    assert result["copiados"]["melhorias"] == 1
    assert result["copiados"]["revisoes"] == 1
    assert result["copiados"]["medicoes"] == 1
    assert result["copiados"]["investimentos"] == 1
    assert result["copiados"]["vinculos"] == 1
    assert result["copiados"]["diagramas_macro"] == 1
    assert result["copiados"]["decomposicao"] == 1
    assert result["copiados"]["escopos_diagrama"] == 1
    assert result["copiados"]["escopos_decomposicao"] == 1
    assert result["copiados"]["overlays_diagrama"] == 1
    assert result["copiados"]["overlays_decomposicao"] == 1
    assert result["copiados"]["evidencias"] == 1
    conn.commit.assert_called_once()
    inst_repo.update_contexto.assert_called_once()
    diagram_repo.upsert_from_backup.assert_called_once()
    decomp_repo.upsert_from_backup.assert_called_once()
    evidence_storage.copy_file.assert_called_once()


@patch("tm_app.application.services.processo_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoInstanciaRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoDiagramRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoDecomposicaoRepository")
@patch("tm_app.application.services.processo_duplicate_service.ProcessoRepository")
def test_duplicate_allows_process_without_melhorias(
    mock_proc_cls,
    mock_decomp_cls,
    mock_diagram_cls,
    mock_inst_cls,
    mock_conn_factory,
):
    conn = MagicMock()
    mock_conn_factory.return_value = conn

    proc_repo = mock_proc_cls.return_value
    inst_repo = mock_inst_cls.return_value
    diagram_repo = mock_diagram_cls.return_value
    decomp_repo = mock_decomp_cls.return_value

    proc_repo.get.return_value = {
        "processo_id": "p-old",
        "nome_processo": "Processo vazio",
        "status_processo": "ativo",
    }
    inst_repo.list_by_processo.return_value = []
    proc_repo.create.return_value = {
        "processo_id": "p-new",
        "nome_processo": "Processo vazio (cópia)",
    }
    diagram_repo.get.return_value = {"conteudo": {"nodes": []}, "mermaid_cached": None}

    result = ProcessoDuplicateService().duplicate("p-old")

    assert result["copiados"]["melhorias"] == 0
    assert result["copiados"]["diagramas_macro"] == 1
    conn.commit.assert_called_once()


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
