from __future__ import annotations

from datetime import date
from unittest.mock import patch

from tm_app.application.services.diagrama_composition_service import DiagramaCompositionService


def _sample_macro():
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "n1", "type": "process", "label": "Entrada", "position": {"x": 0, "y": 0}},
            {"id": "n2", "type": "process", "label": "Saída", "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from": "n1", "to": "n2", "label": None}],
    }


@patch("tm_app.application.services.diagrama_composition_service.RevisaoDiagramOverlayRepository")
@patch("tm_app.application.services.diagrama_composition_service.InstanciaDiagramEscopoRepository")
@patch("tm_app.application.services.diagrama_composition_service.RevisaoRepository")
@patch("tm_app.application.services.diagrama_composition_service.ProcessoDiagramRepository")
def test_compose_applies_newer_label_and_conflict(
    mock_proc,
    mock_rev,
    mock_escopo,
    mock_overlay,
):
    mock_proc.return_value.get.return_value = {"conteudo": _sample_macro()}
    mock_rev.return_value.list_by_processo.return_value = [
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
    mock_escopo.return_value.get.return_value = {
        "node_ids": [],
        "inherit_all": True,
        "include_boundary_edges": False,
    }

    def overlay_get(revisao_id: str):
        if revisao_id == "r1":
            return {
                "conteudo": {
                    "format": "flowchart_overlay_v1",
                    "format_version": 1,
                    "node_overrides": {"n1": {"label": "A", "highlight": "tobe"}},
                }
            }
        return {
            "conteudo": {
                "format": "flowchart_overlay_v1",
                "format_version": 1,
                "node_overrides": {"n1": {"label": "B", "highlight": "tobe"}},
            }
        }

    mock_overlay.return_value.get.side_effect = overlay_get

    result = DiagramaCompositionService().compose_for_processo("p1", at=date(2026, 5, 1))
    labels = {n["id"]: n["label"] for n in result["flowchart"]["nodes"]}
    assert labels["n1"] == "B"
    assert len(result["conflicts"]) == 1
    assert result["conflicts"][0]["winner_revisao_id"] == "r2"
    assert len(result["applied_revisoes"]) == 2
