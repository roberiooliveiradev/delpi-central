from __future__ import annotations

from tm_app.application.services.decomposition_flat_export_service import (
    DecompositionFlatExportService,
)
from tm_app.application.services.revisao_decomposicao_merge_service import (
    RevisaoDecomposicaoMergeService,
)
from tm_app.domain.decomposition.decomposition_tree_v1 import DecompositionValidationError
import pytest


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
        ],
    }


def test_merge_applies_scope_subset():
    merged = RevisaoDecomposicaoMergeService().merge(
        tree=_sample_tree(),
        escopo={"node_ids": ["pk_crm"], "inherit_all": False, "include_descendants": True},
        overlay=None,
    )
    ids = {node["id"] for node in merged["tree"]["nodes"]}
    assert ids == {"pk_crm", "st_notificacao"}


def test_merge_applies_overlay_label():
    merged = RevisaoDecomposicaoMergeService().merge(
        tree=_sample_tree(),
        escopo={"inherit_all": True},
        overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {
                "st_notificacao": {"label": "Notificação automática", "highlight": "tobe"},
            },
        },
    )
    labels = [node["label"] for node in merged["tree"]["nodes"]]
    assert "Notificação automática" in labels


def test_merge_applies_extra_node_and_disable():
    merged = RevisaoDecomposicaoMergeService().merge(
        tree=_sample_tree(),
        escopo={"inherit_all": True},
        overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "disabled_node_ids": ["st_notificacao"],
            "extra_nodes": [
                {
                    "id": "st_auto",
                    "level": "sub_tarefa",
                    "ordem": 9,
                    "label": "Disparo automático",
                    "parent_id": "pk_crm",
                    "highlight": "tobe",
                }
            ],
        },
    )
    ids = {node["id"] for node in merged["tree"]["nodes"]}
    assert "st_notificacao" not in ids
    assert "st_auto" in ids
    assert "tree_base" in merged
    assert "st_notificacao" in {n["id"] for n in merged["tree_base"]["nodes"]}


def test_assert_extra_outside_parent_raises():
    with pytest.raises(DecompositionValidationError, match="parent_id"):
        RevisaoDecomposicaoMergeService().assert_overlay_within_escopo(
            tree=_sample_tree(),
            escopo={
                "node_ids": ["st_notificacao"],
                "inherit_all": False,
                "include_descendants": False,
            },
            overlay={
                "format": "decomposition_overlay_v1",
                "format_version": 1,
                "extra_nodes": [
                    {
                        "id": "st_novo",
                        "level": "sub_tarefa",
                        "ordem": 1,
                        "label": "Novo",
                        "parent_id": "pk_crm",
                    }
                ],
            },
        )


def test_build_revisao_view_seeds_from_reference_when_overlay_empty():
    tree = _sample_tree()
    reference_overlay = {
        "format": "decomposition_overlay_v1",
        "format_version": 1,
        "node_overrides": {
            "st_notificacao": {"label": "Notificação da referência", "highlight": "tobe"},
        },
    }
    view = RevisaoDecomposicaoMergeService().build_revisao_view(
        tree=tree,
        escopo={"inherit_all": True},
        overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {},
            "disabled_node_ids": [],
            "extra_nodes": [],
        },
        reference_overlay=reference_overlay,
        reference_meta={
            "revisao_id": "ref-1",
            "versao_revisao": "1.0.0",
            "cenario_tipo": "melhoria",
        },
    )
    labels = {n["id"]: n["label"] for n in view["tree"]["nodes"]}
    assert labels["st_notificacao"] == "Notificação da referência"
    assert view["seeded_from_reference"] is True
    assert view["referencia"]["versao_revisao"] == "1.0.0"
    base_labels = {n["id"]: n["label"] for n in view["tree_base"]["nodes"]}
    assert base_labels["st_notificacao"] == "Receber notificação"


def test_build_revisao_view_keeps_own_overlay_when_present():
    tree = _sample_tree()
    view = RevisaoDecomposicaoMergeService().build_revisao_view(
        tree=tree,
        escopo={"inherit_all": True},
        overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {
                "st_notificacao": {"label": "Delta desta revisão", "highlight": "tobe"},
            },
        },
        reference_overlay={
            "format": "decomposition_overlay_v1",
            "format_version": 1,
            "node_overrides": {
                "st_notificacao": {"label": "Da referência", "highlight": "tobe"},
            },
        },
        reference_meta={"revisao_id": "ref-1", "versao_revisao": "1.0.0"},
    )
    labels = {n["id"]: n["label"] for n in view["tree"]["nodes"]}
    assert labels["st_notificacao"] == "Delta desta revisão"
    assert view["seeded_from_reference"] is False
    assert view["reference_diff"]["changed"] == ["st_notificacao"]


def test_export_flat_rows_legacy_format():
    rows = DecompositionFlatExportService().build_rows(
        tree=_sample_tree(),
        macroprocesso="LMP",
        departamento="Engenharia",
    )
    assert len(rows) == 1
    assert rows[0]["departamento"] == "Engenharia"
    assert rows[0]["macroprocesso"] == "LMP"
    assert rows[0]["num_processo_chave"] == "1"
    assert rows[0]["sub_tarefas"] == "Receber notificação"


def test_export_csv_has_header():
    rows = DecompositionFlatExportService().build_rows(
        tree=_sample_tree(),
        macroprocesso="LMP",
        departamento="Engenharia",
    )
    csv_text = DecompositionFlatExportService().to_csv(rows)
    assert "departamento" in csv_text.splitlines()[0]
    assert "Engenharia" in csv_text
