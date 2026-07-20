from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.services.decomposicao_composition_service import (
    DecomposicaoCompositionService,
    revisao_vigente_em,
)
from tm_app.application.services.revisao_decomposicao_merge_service import (
    RevisaoDecomposicaoMergeService,
)
from tm_app.domain.decomposition.decomposition_tree_v1 import DecompositionValidationError


def _sample_tree():
    return {
        "format": "decomposition_tree_v1",
        "format_version": 1,
        "nodes": [
            {
                "id": "pk_crm",
                "level": "processo_chave",
                "ordem": 1,
                "label": "Recebimento CRM",
                "parent_id": None,
            },
            {
                "id": "st_notificacao",
                "level": "sub_tarefa",
                "ordem": 1,
                "label": "Receber notificação",
                "parent_id": "pk_crm",
            },
            {
                "id": "st_arquivo",
                "level": "sub_tarefa",
                "ordem": 2,
                "label": "Arquivar",
                "parent_id": "pk_crm",
            },
        ],
    }


def test_assert_overlay_within_escopo_ok():
    overlay = RevisaoDecomposicaoMergeService().assert_overlay_within_escopo(
        tree=_sample_tree(),
        escopo={"node_ids": ["pk_crm"], "inherit_all": False, "include_descendants": True},
        overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {
                "st_notificacao": {"label": "Auto", "highlight": "tobe"},
            },
        },
    )
    assert "st_notificacao" in overlay["node_overrides"]


def test_assert_overlay_outside_escopo_raises():
    with pytest.raises(DecompositionValidationError, match="fora do escopo"):
        RevisaoDecomposicaoMergeService().assert_overlay_within_escopo(
            tree=_sample_tree(),
            escopo={"node_ids": ["st_arquivo"], "inherit_all": False, "include_descendants": False},
            overlay={
                "format": "decomposition_overlay_v1",
                "format_version": 1,
                "node_overrides": {
                    "st_notificacao": {"label": "Fora"},
                },
            },
        )


def test_revisao_vigente_em_janela():
    rev = {
        "cenario_tipo": "automacao",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-06-30",
        "deletado": False,
    }
    assert revisao_vigente_em(rev, date(2026, 3, 15)) is True
    assert revisao_vigente_em(rev, date(2025, 12, 31)) is False
    assert revisao_vigente_em(rev, date(2026, 7, 1)) is False
    assert revisao_vigente_em({**rev, "cenario_tipo": "baseline"}, date(2026, 3, 15)) is False


@patch("tm_app.application.services.decomposicao_composition_service.RevisaoDecomposicaoOverlayRepository")
@patch("tm_app.application.services.decomposicao_composition_service.InstanciaDecomposicaoEscopoRepository")
@patch("tm_app.application.services.decomposicao_composition_service.RevisaoRepository")
@patch("tm_app.application.services.decomposicao_composition_service.ProcessoDecomposicaoRepository")
def test_compose_applies_newer_label_and_detects_conflict(
    mock_proc_decomp,
    mock_revisao_repo,
    mock_escopo_repo,
    mock_overlay_repo,
):
    mock_proc_decomp.return_value.get.return_value = {"conteudo": _sample_tree()}
    mock_revisao_repo.return_value.list_by_processo.return_value = [
        {
            "revisao_id": "r1",
            "instancia_id": "i1",
            "versao_revisao": "1.0.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-01-01",
            "data_fim_vigencia": None,
            "deletado": False,
        },
        {
            "revisao_id": "r2",
            "instancia_id": "i2",
            "versao_revisao": "2.0.0",
            "cenario_tipo": "automacao",
            "data_inicio_vigencia": "2026-04-01",
            "data_fim_vigencia": None,
            "deletado": False,
        },
    ]

    def escopo_get(instancia_id: str):
        return {
            "node_ids": [],
            "inherit_all": True,
            "include_descendants": True,
        }

    mock_escopo_repo.return_value.get.side_effect = escopo_get

    def overlay_get(revisao_id: str):
        if revisao_id == "r1":
            return {
                "conteudo": {
                    "format": "decomposition_overlay_v1",
                    "format_version": 1,
                    "node_overrides": {
                        "st_notificacao": {"label": "Label A", "highlight": "tobe"},
                    },
                }
            }
        return {
            "conteudo": {
                "format": "decomposition_overlay_v1",
                "format_version": 1,
                "node_overrides": {
                    "st_notificacao": {"label": "Label B", "highlight": "tobe"},
                },
            }
        }

    mock_overlay_repo.return_value.get.side_effect = overlay_get

    result = DecomposicaoCompositionService().compose_for_processo(
        "p1",
        at=date(2026, 5, 1),
    )
    labels = {n["id"]: n["label"] for n in result["tree"]["nodes"]}
    assert labels["st_notificacao"] == "Label B"
    assert len(result["conflicts"]) == 1
    assert result["conflicts"][0]["field"] == "label"
    assert result["conflicts"][0]["winner_revisao_id"] == "r2"
    assert len(result["applied_revisoes"]) == 2


@patch("tm_app.application.services.decomposicao_composition_service.RevisaoDecomposicaoOverlayRepository")
@patch("tm_app.application.services.decomposicao_composition_service.InstanciaDecomposicaoEscopoRepository")
@patch("tm_app.application.services.decomposicao_composition_service.RevisaoRepository")
@patch("tm_app.application.services.decomposicao_composition_service.ProcessoDecomposicaoRepository")
def test_compose_skips_non_vigente(
    mock_proc_decomp,
    mock_revisao_repo,
    mock_escopo_repo,
    mock_overlay_repo,
):
    mock_proc_decomp.return_value.get.return_value = {"conteudo": _sample_tree()}
    mock_revisao_repo.return_value.list_by_processo.return_value = [
        {
            "revisao_id": "r_old",
            "instancia_id": "i1",
            "versao_revisao": "1.0.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2025-01-01",
            "data_fim_vigencia": "2025-12-31",
            "deletado": False,
        },
    ]
    mock_escopo_repo.return_value.get.return_value = {
        "node_ids": [],
        "inherit_all": True,
        "include_descendants": True,
    }
    mock_overlay_repo.return_value.get.return_value = {
        "conteudo": {
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {
                "st_notificacao": {"label": "Não deve aparecer"},
            },
        }
    }

    result = DecomposicaoCompositionService().compose_for_processo(
        "p1",
        at=date(2026, 5, 1),
    )
    labels = {n["id"]: n["label"] for n in result["tree"]["nodes"]}
    assert labels["st_notificacao"] == "Receber notificação"
    assert result["applied_revisoes"] == []
    assert result["conflicts"] == []
