"""TM-GPI-002 — governed WBS writes + legacy flowchart_v1 read-only lock.

Legacy diagram writes (process_diagram / instance_diagram_scope /
revision_diagram_overlay) are intentionally impossible via TÉO/GPT surfaces:
the entity catalog no longer advertises create/update, generic record writes
fail the capability gate, and DiagramWriteService was removed with the last
internal save path. New diagrams are native BPMN (Portal authority).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.entities import GptEntity
from tm_app.application.services.decomposition_write_service import (
    DecompositionWriteError,
    DecompositionWriteService,
)


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


@pytest.mark.parametrize(
    "entity_value",
    ["process_diagram", "instance_diagram_scope", "revision_diagram_overlay"],
)
def test_legacy_diagram_create_rejected(entity_value):
    request = MagicMock()
    svc = GptActionsDispatchService()
    with pytest.raises(GptActionsError) as exc:
        svc.create_record(request, entity_value, {"conteudo": {}})
    assert exc.value.status_code == 400
    assert "does not support 'create'" in str(exc.value)


@pytest.mark.parametrize(
    "entity_value",
    ["process_diagram", "instance_diagram_scope", "revision_diagram_overlay"],
)
def test_legacy_diagram_update_rejected(entity_value):
    request = MagicMock()
    svc = GptActionsDispatchService()
    with pytest.raises(GptActionsError) as exc:
        svc.update_record(request, entity_value, "some-id", {"conteudo": {}})
    assert exc.value.status_code == 400
    assert "does not support 'update'" in str(exc.value)


def test_diagram_write_service_removed():
    """No internal legacy save path may survive the convergence."""
    with pytest.raises(ModuleNotFoundError):
        __import__("tm_app.application.services.diagram_write_service")


def test_decomposition_save_tree_valid_and_invalid():
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    with (
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.services.decomposition_write_service.ProcessoDecomposicaoRepository"
        ) as decomp,
        patch(
            "tm_app.application.services.decomposition_write_service.touch_processo_updated_at"
        ) as touch,
    ):
        proc.return_value.get.return_value = {"processo_id": pid}
        decomp.return_value.get.return_value = None
        decomp.return_value.upsert.side_effect = lambda *a, **kw: {
            "processo_id": pid,
            "conteudo": kw["conteudo"],
        }
        saved = DecompositionWriteService().save_tree(pid, _valid_tree())
        assert saved["nodes"] == 2
        touch.assert_called_once_with(pid)

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
        assert touch.call_count == 1


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


def test_gpt_upsert_process_diagram_blocked_read_only():
    """Even a direct internal call cannot persist legacy flowchart_v1."""
    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    svc = GptActionsDispatchService()
    with pytest.raises(GptActionsError) as exc:
        svc._upsert_document(
            request,
            GptEntity.PROCESS_DIAGRAM,
            pid,
            {"conteudo": {"format": "flowchart_v1", "nodes": [], "edges": []}},
        )
    assert exc.value.status_code == 400


def test_gpt_upsert_view_without_manage_is_403():
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
        patch.object(svc._decomp_writes, "save_tree") as save,
    ):
        with pytest.raises(GptActionsError) as exc:
            svc._upsert_document(
                request,
                GptEntity.DECOMPOSITION_TREE,
                pid,
                {"conteudo": _valid_tree()},
            )
        assert exc.value.status_code == 403
        save.assert_not_called()


def test_gpt_upsert_decomposition_tree_valid():
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
