"""Process update PATCH/merge: omit keeps; explicit null clears (not codigo)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tm_app.application.services.process_write_service import (
    ProcessWriteService,
    process_master_update_payload,
)
from tm_app.interface.http.schemas.crud_schemas import ProcessoUpdateBody


def _current(**overrides):
    row = {
        "processo_id": "p1",
        "codigo_processo": "PROC-0071",
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "descricao_processo": "Descrição original",
        "gestor_responsavel": "Michael Moarotto e Robério Oliveira",
        "objetivo_processo": "Objetivo original",
        "familia_processo": None,
        "agrupador_ferramenta": None,
    }
    row.update(overrides)
    return row


def test_merge_omitted_optional_keeps_current():
    provided = {
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "codigo_processo": "PROC-0001",
    }
    payload = process_master_update_payload(provided, _current())
    assert payload["codigo_processo"] == "PROC-0001"
    assert payload["descricao_processo"] == "Descrição original"
    assert payload["gestor_responsavel"] == "Michael Moarotto e Robério Oliveira"
    assert payload["objetivo_processo"] == "Objetivo original"
    assert payload["familia_processo"] is None
    assert payload["agrupador_ferramenta"] is None


def test_merge_explicit_null_clears_optional():
    provided = {
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "descricao_processo": None,
        "gestor_responsavel": None,
        "objetivo_processo": None,
    }
    payload = process_master_update_payload(provided, _current())
    assert payload["descricao_processo"] is None
    assert payload["gestor_responsavel"] is None
    assert payload["objetivo_processo"] is None
    assert payload["codigo_processo"] is None  # omit → COALESCE keep


def test_merge_blank_string_clears_optional():
    provided = {
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "gestor_responsavel": "   ",
    }
    payload = process_master_update_payload(provided, _current())
    assert payload["gestor_responsavel"] is None
    assert payload["descricao_processo"] == "Descrição original"


def test_merge_codigo_null_does_not_clear():
    provided = {
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "codigo_processo": None,
    }
    payload = process_master_update_payload(provided, _current())
    assert payload["codigo_processo"] is None  # repository COALESCE preserves


def test_observed_codigo_change_preserves_objetivo_descricao_gestor():
    """Regression: changing codigo alone must not wipe filled optional fields."""
    svc = ProcessWriteService()
    body = ProcessoUpdateBody.model_validate(
        {
            "nome_processo": "Processo X",
            "status_processo": "ativo",
            "codigo_processo": "PROC-0001",
        }
    )
    assert "descricao_processo" not in body.model_fields_set
    current = _current()
    updated = {
        **current,
        "codigo_processo": "PROC-0001",
    }
    with patch(
        "tm_app.application.services.process_write_service.ProcessoRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.get.side_effect = [current, updated]
        repo.update.return_value = updated
        row = svc.update("p1", body, save_escopo=lambda *_a, **_k: None)
    payload = repo.update.call_args.args[1]
    assert payload["codigo_processo"] == "PROC-0001"
    assert payload["descricao_processo"] == "Descrição original"
    assert payload["objetivo_processo"] == "Objetivo original"
    assert payload["gestor_responsavel"] == "Michael Moarotto e Robério Oliveira"
    assert row["codigo_processo"] == "PROC-0001"


def test_update_explicit_null_clears_gestor():
    svc = ProcessWriteService()
    body = ProcessoUpdateBody.model_validate(
        {
            "nome_processo": "Processo X",
            "status_processo": "ativo",
            "gestor_responsavel": None,
        }
    )
    assert "gestor_responsavel" in body.model_fields_set
    current = _current()
    updated = {**current, "gestor_responsavel": None}
    with patch(
        "tm_app.application.services.process_write_service.ProcessoRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.get.side_effect = [current, updated]
        repo.update.return_value = updated
        svc.update("p1", body, save_escopo=lambda *_a, **_k: None)
    payload = repo.update.call_args.args[1]
    assert payload["gestor_responsavel"] is None
    assert payload["descricao_processo"] == "Descrição original"


def test_gpt_update_codigo_preserves_optional_fields():
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    dispatch = GptActionsDispatchService()
    request = MagicMock()
    request.state.user = SimpleNamespace(id="u1", permissions=[], is_superadmin=True)
    current = _current()
    updated = {**current, "codigo_processo": "PROC-0001"}
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_view_access",
            return_value=None,
        ),
        patch.object(dispatch, "_validate_processo_escopo_access", return_value=None),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessWriteService"
        ) as svc_cls,
        patch.object(dispatch, "_audit") as audit,
        patch.object(dispatch._recalc_hook, "after_processo"),
    ):
        svc_cls.return_value.update.return_value = updated
        result, message = dispatch.update_record(
            request,
            "process",
            "p1",
            {
                "data": {
                    "nome_processo": "Processo X",
                    "status_processo": "ativo",
                    "codigo_processo": "PROC-0001",
                }
            },
        )
    assert result["codigo_processo"] == "PROC-0001"
    assert "atualizado" in message.lower()
    audited = audit.call_args.args[4]
    assert "codigo_processo" in audited
    assert "descricao_processo" not in audited
    assert "gestor_responsavel" not in audited
    assert "objetivo_processo" not in audited


def test_pydantic_omit_vs_explicit_null_fields_set():
    omitted = ProcessoUpdateBody.model_validate(
        {"nome_processo": "X", "status_processo": "ativo"}
    )
    cleared = ProcessoUpdateBody.model_validate(
        {
            "nome_processo": "X",
            "status_processo": "ativo",
            "objetivo_processo": None,
        }
    )
    assert "objetivo_processo" not in omitted.model_fields_set
    assert "objetivo_processo" in cleared.model_fields_set
    assert cleared.objetivo_processo is None
