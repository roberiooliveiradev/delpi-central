from __future__ import annotations

from tm_app.application.services.decomposition_flat_export_service import (
    DecompositionFlatExportService,
)
from tm_app.application.services.revisao_decomposicao_merge_service import (
    RevisaoDecomposicaoMergeService,
)


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
