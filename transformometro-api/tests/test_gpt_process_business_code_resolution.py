"""Business-code resolution for process-scoped reads — INT-1 front A.

``decomposition_tree.get`` (and siblings) previously cast the raw
record id to ``::uuid`` in the repository, so a user-facing business
code (``PROC-XXXX``) failed before any domain evidence was read.
The dispatch layer now normalizes the reference through the canonical
``ProcessoRepository.get`` resolver — the same lookup ``process.get``
already used — before access checks and document repositories.

Positive: business code resolves to the authoritative UUID.
Sibling: a raw UUID follows the identical resolution path.
Negative: an unknown reference fails closed with 404 before any
document repository or access-check bypass.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.entities import GptEntity

_MODULE = "tm_app.application.gpt_actions.dispatch_service"
_PROC_UUID = "9f1c2d34-0000-4000-8000-0000000000aa"


def _svc() -> GptActionsDispatchService:
    return GptActionsDispatchService()


def _processo_repo_row(*, code: str = "PROC-0034") -> dict:
    return {
        "processo_id": _PROC_UUID,
        "codigo_processo": code,
        "nome_processo": "DELPI Indicadores",
    }


def test_decomposition_tree_get_accepts_business_code():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.ProcessoDecomposicaoRepository"
        ) as decomp_repo_cls,
        patch(
            f"{_MODULE}.check_processo_view_access",
            return_value=None,
        ) as access,
    ):
        proc_repo_cls.return_value.get.return_value = (
            _processo_repo_row()
        )
        decomp_repo_cls.return_value.get.return_value = {
            "processo_id": _PROC_UUID,
            "conteudo": {"nodes": []},
        }
        out = svc.get_record(
            MagicMock(), "decomposition_tree", "PROC-0034"
        )
    # The canonical resolver received the business code…
    proc_repo_cls.return_value.get.assert_called_once_with("PROC-0034")
    # …and the document path ran on the authoritative UUID.
    access.assert_called_once()
    assert access.call_args.args[1] == _PROC_UUID
    decomp_repo_cls.return_value.get.assert_called_once_with(_PROC_UUID)
    assert out["processo_id"] == _PROC_UUID
    # Resolved business identity is echoed — the owner attests the
    # code↔document binding the caller asked about.
    assert out["codigo_processo"] == "PROC-0034"
    assert out["nome_processo"] == "DELPI Indicadores"


def test_decomposition_tree_get_accepts_uuid():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.ProcessoDecomposicaoRepository"
        ) as decomp_repo_cls,
        patch(
            f"{_MODULE}.check_processo_view_access",
            return_value=None,
        ),
    ):
        proc_repo_cls.return_value.get.return_value = (
            _processo_repo_row()
        )
        decomp_repo_cls.return_value.get.return_value = {
            "processo_id": _PROC_UUID,
            "conteudo": {},
        }
        svc.get_record(
            MagicMock(), "decomposition_tree", _PROC_UUID
        )
    decomp_repo_cls.return_value.get.assert_called_once_with(_PROC_UUID)


def test_decomposition_tree_unknown_reference_fails_closed():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.ProcessoDecomposicaoRepository"
        ) as decomp_repo_cls,
        patch(
            f"{_MODULE}.check_processo_view_access",
            return_value=None,
        ) as access,
    ):
        proc_repo_cls.return_value.get.return_value = None
        with pytest.raises(GptActionsError) as exc:
            svc.get_record(
                MagicMock(), "decomposition_tree", "PROC-9999"
            )
    assert exc.value.status_code == 404
    access.assert_not_called()
    decomp_repo_cls.return_value.get.assert_not_called()


def test_process_diagram_get_accepts_business_code():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.ProcessoDiagramRepository"
        ) as diagram_repo_cls,
        patch(
            f"{_MODULE}.check_processo_view_access",
            return_value=None,
        ),
    ):
        proc_repo_cls.return_value.get.return_value = (
            _processo_repo_row()
        )
        diagram_repo_cls.return_value.get.return_value = {
            "processo_id": _PROC_UUID
        }
        out = svc.get_record(
            MagicMock(), "process_diagram", "PROC-0034"
        )
    diagram_repo_cls.return_value.get.assert_called_once_with(_PROC_UUID)
    assert out["processo_id"] == _PROC_UUID


def test_analyze_process_scoped_view_resolves_business_code():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.check_processo_view_access",
            return_value=None,
        ) as access,
        patch.object(
            svc, "_analyze_view", return_value={"view": "ok"}
        ) as analyze,
    ):
        proc_repo_cls.return_value.get.return_value = (
            _processo_repo_row()
        )
        out = svc.analyze(
            MagicMock(),
            view="diagram_validation",
            processo_id="PROC-0034",
        )
    assert out == {"view": "ok"}
    assert access.call_args.args[1] == _PROC_UUID
    assert analyze.call_args.kwargs["processo_id"] == _PROC_UUID


def test_upsert_decomposition_tree_resolves_business_code():
    svc = _svc()
    with (
        patch(
            f"{_MODULE}.ProcessoRepository"
        ) as proc_repo_cls,
        patch(
            f"{_MODULE}.check_processo_manage_access",
            return_value=None,
        ) as access,
        patch.object(
            svc._decomp_writes,
            "save_tree",
            return_value={"row": {"processo_id": _PROC_UUID},
                          "nodes": 0,
                          "conteudo": {}},
        ) as save,
        patch.object(
            svc._decomp_writes,
            "read_back_tree",
            return_value={"conteudo": {}},
        ),
        patch.object(svc, "_audit"),
        patch(
            f"{_MODULE}.row_to_json",
            side_effect=lambda d: d,
        ),
    ):
        proc_repo_cls.return_value.get.return_value = (
            _processo_repo_row()
        )
        out, message, status = svc._upsert_document(
            MagicMock(),
            GptEntity.DECOMPOSITION_TREE,
            "PROC-0034",
            {"conteudo": {}},
        )
    assert access.call_args.args[1] == _PROC_UUID
    save.assert_called_once()
    assert save.call_args.args[0] == _PROC_UUID
    assert out["persisted"] is True
