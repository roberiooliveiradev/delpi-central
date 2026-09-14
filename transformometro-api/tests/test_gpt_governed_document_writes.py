"""TM-GPI-002 — governed diagram/WBS writes (canonical validation + AuthZ + verify)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.services.decomposition_write_service import (
    DecompositionWriteError,
    DecompositionWriteService,
)
from tm_app.application.services.diagram_write_service import (
    DiagramWriteError,
    DiagramWriteService,
)
from tm_app.domain.decomposition.decomposition_tree_v1 import empty_tree
from tm_app.domain.diagram.flowchart_v1 import empty_flowchart, empty_overlay


def _valid_macro() -> dict:
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "lanes": [{"id": "lane_a", "label": "Comercial", "height": 168}],
        "nodes": [
            {
                "id": "n_start",
                "type": "start",
                "label": "Início",
                "lane_id": "lane_a",
                "position": {"x": 160, "y": 60},
            },
            {
                "id": "n_proc",
                "type": "process",
                "label": "Atividade",
                "lane_id": "lane_a",
                "position": {"x": 320, "y": 50},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "from": "n_start",
                "to": "n_proc",
                "label": None,
                "routing": "smoothstep",
            }
        ],
    }


def _valid_tree() -> dict:
    return {
        "format": "decomposition_tree_v1",
        "format_version": 1,
        "nodes": [
            {
                "id": "pk_1",
                "level": "processo_chave",
                "ordem": 1,
                "label": "Chave",
                "parent_id": None,
            },
            {
                "id": "st_1",
                "level": "sub_tarefa",
                "ordem": 1,
                "label": "Sub",
                "parent_id": "pk_1",
            },
        ],
    }


def test_diagram_prepare_macro_valid_no_persist():
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoDiagramRepository"
        ) as diag,
    ):
        proc.return_value.get.return_value = {"processo_id": pid}
        diag.return_value.get.return_value = None
        prepared = DiagramWriteService().prepare_macro(pid, _valid_macro())
        assert prepared["valid"] is True
        assert prepared["persisted"] is False
        assert prepared["mermaid"]
        diag.return_value.upsert.assert_not_called()


def test_diagram_save_macro_rejects_invalid_and_does_not_write():
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoDiagramRepository"
        ) as diag,
    ):
        proc.return_value.get.return_value = {"processo_id": pid}
        with pytest.raises(DiagramWriteError):
            DiagramWriteService().save_macro(
                pid,
                {
                    "format": "flowchart_v1",
                    "format_version": 1,
                    "nodes": [{"id": "bad"}],
                    "edges": [{"id": "e1", "from": "x", "to": "y"}],
                },
            )
        diag.return_value.upsert.assert_not_called()


def test_diagram_save_macro_server_derives_mermaid_ignores_client_cache():
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    macro = _valid_macro()
    with (
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoDiagramRepository"
        ) as diag,
    ):
        proc.return_value.get.return_value = {"processo_id": pid}
        diag.return_value.get.return_value = None
        diag.return_value.upsert.side_effect = lambda *a, **kw: {
            "processo_id": pid,
            "conteudo": kw["conteudo"],
            "mermaid_cached": kw["mermaid_cached"],
        }
        saved = DiagramWriteService().save_macro(
            pid, {**macro, "mermaid_cached": "flowchart TD; FAKE"}
        )
        assert saved["mermaid"] != "flowchart TD; FAKE"
        assert "FAKE" not in (saved["mermaid"] or "")
        assert diag.return_value.upsert.call_args.kwargs["mermaid_cached"] == saved[
            "mermaid"
        ]


def test_diagram_instance_scope_rejects_unknown_macro_node():
    iid = "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoInstanciaRepository"
        ) as inst,
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoDiagramRepository"
        ) as diag,
        patch(
            "tm_app.application.services.diagram_write_service.InstanciaDiagramEscopoRepository"
        ) as escopo,
    ):
        inst.return_value.get.return_value = {
            "instancia_id": iid,
            "processo_id": pid,
        }
        diag.return_value.get.return_value = {"conteudo": _valid_macro()}
        with pytest.raises(DiagramWriteError):
            DiagramWriteService().save_instance_scope(
                iid,
                {
                    "node_ids": ["does_not_exist"],
                    "inherit_all": False,
                    "include_boundary_edges": False,
                },
            )
        escopo.return_value.upsert.assert_not_called()


def test_diagram_revision_overlay_invalid_no_write():
    rid = "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr"
    with patch.object(
        DiagramWriteService,
        "_load_merge_context",
        return_value=(
            {"revisao_id": rid, "processo_id": "p"},
            _valid_macro(),
            {"node_ids": [], "inherit_all": True, "include_boundary_edges": False},
            None,
        ),
    ):
        with patch(
            "tm_app.application.services.diagram_write_service.RevisaoDiagramOverlayRepository"
        ) as overlay_repo:
            with pytest.raises(DiagramWriteError):
                DiagramWriteService().save_revision_overlay(
                    rid,
                    {"format": "not_an_overlay", "format_version": 1},
                )
            overlay_repo.return_value.upsert.assert_not_called()


def test_diagram_revision_overlay_valid_prepare_has_merged_preview():
    rid = "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr"
    overlay = empty_overlay()
    with patch.object(
        DiagramWriteService,
        "_load_merge_context",
        return_value=(
            {"revisao_id": rid, "processo_id": "p"},
            _valid_macro(),
            {"node_ids": [], "inherit_all": True, "include_boundary_edges": False},
            None,
        ),
    ):
        prepared = DiagramWriteService().prepare_revision_overlay(rid, overlay)
        assert prepared["valid"] is True
        assert prepared["persisted"] is False
        assert prepared["merged_preview"] is not None
        assert prepared["mermaid"]


def test_decomposition_save_tree_valid_and_invalid():
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoDecomposicaoRepository"
        ) as decomp,
    ):
        proc.return_value.get.return_value = {"processo_id": pid}
        decomp.return_value.get.return_value = None
        decomp.return_value.upsert.side_effect = lambda *a, **kw: {
            "processo_id": pid,
            "conteudo": kw["conteudo"],
        }
        saved = DecompositionWriteService().save_tree(pid, _valid_tree())
        assert saved["nodes"] == 2

        with pytest.raises(DecompositionWriteError):
            DecompositionWriteService().save_tree(
                pid,
                {
                    "format": "decomposition_tree_v1",
                    "format_version": 1,
                    "nodes": [
                        {
                            "id": "x",
                            "level": "invalid",
                            "ordem": 1,
                            "label": "x",
                            "parent_id": None,
                        }
                    ],
                },
            )


def test_decomposition_instance_scope_rejects_unknown_node():
    iid = "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoInstanciaRepository"
        ) as inst,
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoDecomposicaoRepository"
        ) as tree,
        patch(
            "tm_app.application.services.decomposition_write_service.InstanciaDecomposicaoEscopoRepository"
        ) as escopo,
    ):
        inst.return_value.get.return_value = {
            "instancia_id": iid,
            "processo_id": pid,
        }
        tree.return_value.get.return_value = {"conteudo": _valid_tree()}
        with pytest.raises(DecompositionWriteError):
            DecompositionWriteService().save_instance_scope(
                iid,
                {
                    "node_ids": ["missing"],
                    "inherit_all": False,
                    "include_descendants": True,
                },
            )
        escopo.return_value.upsert.assert_not_called()


def test_gpt_upsert_process_diagram_valid_verifies_read_back():
    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    macro = _valid_macro()
    saved_row = {
        "processo_id": pid,
        "conteudo": macro,
        "mermaid_cached": "flowchart LR\n  n_start-->n_proc",
    }
    svc = GptActionsDispatchService()
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
            return_value=None,
        ),
        patch.object(
            svc._diagram_writes,
            "save_macro",
            return_value={
                "row": saved_row,
                "conteudo": macro,
                "mermaid": saved_row["mermaid_cached"],
                "processo_id": pid,
                "nodes": 2,
            },
        ) as save,
        patch.object(
            svc._diagram_writes,
            "read_back_macro",
            return_value=saved_row,
        ),
        patch.object(svc, "_audit"),
    ):
        data, message, status = svc._upsert_document(
            request,
            __import__(
                "tm_app.application.gpt_actions.entities", fromlist=["GptEntity"]
            ).GptEntity.PROCESS_DIAGRAM,
            pid,
            {"conteudo": macro, "mermaid_cached": "client-should-be-ignored"},
        )
    assert status == 200
    assert data["verified"] is True
    assert data["persisted"] is True
    assert "verificad" in message.lower()
    save.assert_called_once()
    assert save.call_args.args[1] == macro or "conteudo" in str(save.call_args)


def test_gpt_upsert_process_diagram_invalid_no_write():
    from tm_app.application.gpt_actions.entities import GptEntity

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    svc = GptActionsDispatchService()
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
            return_value=None,
        ),
        patch.object(
            svc._diagram_writes,
            "save_macro",
            side_effect=DiagramWriteError("invalid flowchart"),
        ),
        patch(
            "tm_app.application.services.diagram_write_service.ProcessoDiagramRepository"
        ) as diag,
    ):
        with pytest.raises(GptActionsError) as exc:
            svc._upsert_document(
                request,
                GptEntity.PROCESS_DIAGRAM,
                pid,
                {"conteudo": {"format": "flowchart_v1", "nodes": []}},
            )
        assert exc.value.status_code == 400
        diag.return_value.upsert.assert_not_called()


def test_gpt_upsert_view_without_manage_is_403():
    from tm_app.application.gpt_actions.entities import GptEntity
    from tm_app.core.responses import fail

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    svc = GptActionsDispatchService()
    denied = fail("Sem permissão para gerenciar dados nesta unidade.", 403)
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
            return_value=denied,
        ),
        patch.object(svc._diagram_writes, "save_macro") as save,
    ):
        with pytest.raises(GptActionsError) as exc:
            svc._upsert_document(
                request,
                GptEntity.PROCESS_DIAGRAM,
                pid,
                {"conteudo": empty_flowchart()},
            )
        assert exc.value.status_code == 403
        save.assert_not_called()


def test_gpt_upsert_decomposition_tree_valid():
    from tm_app.application.gpt_actions.entities import GptEntity

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    tree = _valid_tree()
    row = {"processo_id": pid, "conteudo": tree}
    svc = GptActionsDispatchService()
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
            return_value=None,
        ),
        patch.object(
            svc._decomp_writes,
            "save_tree",
            return_value={"row": row, "conteudo": tree, "processo_id": pid, "nodes": 2},
        ),
        patch.object(svc._decomp_writes, "read_back_tree", return_value=row),
        patch.object(svc, "_audit"),
    ):
        data, message, status = svc._upsert_document(
            request,
            GptEntity.DECOMPOSITION_TREE,
            pid,
            {"conteudo": tree},
        )
    assert status == 200
    assert data["verified"] is True
    assert "verificad" in message.lower()


def test_specialist_instructions_require_confirmation_before_write():
    from pathlib import Path

    text = Path(
        "docs/gpt-actions/specialist-instructions.md"
    ).read_text(encoding="utf-8")
    assert "confirmação" in text.lower() or "confirmar" in text.lower()
    assert "PREPARE" in text or "prepare" in text.lower()
    # After TM-GPI-002, persistence is governed — not blanket-disabled.
    assert "persistência via GPT ainda desabilitada" not in text.lower()
