"""TM-GPI-008 — codigo_processo mutable on process update; processo_id immutable."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.services.process_write_service import (
    ProcessWriteError,
    ProcessWriteService,
    process_master_payload,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.interface.http.schemas.crud_schemas import ProcessoUpdateBody


def _body(**overrides):
    data = {
        "nome_processo": "Processo X",
        "status_processo": "ativo",
        "descricao_processo": "desc",
        "gestor_responsavel": None,
        "objetivo_processo": None,
        "familia_processo": None,
        "agrupador_ferramenta": None,
    }
    data.update(overrides)
    return ProcessoUpdateBody.model_validate(data)


def test_process_master_payload_includes_codigo_processo():
    body = _body(codigo_processo="PROC-0071")
    master = process_master_payload(body)
    assert master["codigo_processo"] == "PROC-0071"
    for key in (
        "nome_processo",
        "descricao_processo",
        "gestor_responsavel",
        "objetivo_processo",
        "status_processo",
        "familia_processo",
        "agrupador_ferramenta",
    ):
        assert key in master


def test_repository_update_sql_sets_codigo_processo_with_coalesce():
    repo = ProcessoRepository(connection=MagicMock())
    repo.execute_returning_one = MagicMock(return_value={"processo_id": "p1"})
    repo.get = MagicMock(
        return_value={
            "processo_id": "p1",
            "codigo_processo": "PROC-0071",
            "nome_processo": "Novo",
        }
    )
    repo.update(
        "p1",
        {
            "nome_processo": "Novo",
            "status_processo": "ativo",
            "codigo_processo": "PROC-0071",
            "descricao_processo": None,
            "gestor_responsavel": None,
            "objetivo_processo": None,
            "familia_processo": None,
            "agrupador_ferramenta": None,
        },
    )
    sql = repo.execute_returning_one.call_args.args[0]
    params = repo.execute_returning_one.call_args.args[1]
    assert "codigo_processo = COALESCE(%s, codigo_processo)" in sql
    assert params[0] == "PROC-0071"
    assert "WHERE processo_id = %s" in sql


def test_repository_update_blank_codigo_preserves_via_null_coalesce():
    repo = ProcessoRepository(connection=MagicMock())
    repo.execute_returning_one = MagicMock(return_value={"processo_id": "p1"})
    repo.get = MagicMock(return_value={"processo_id": "p1", "codigo_processo": "PROC-0001"})
    repo.update(
        "p1",
        {
            "nome_processo": "Novo",
            "status_processo": "ativo",
            "codigo_processo": "   ",
            "descricao_processo": None,
            "gestor_responsavel": None,
            "objetivo_processo": None,
            "familia_processo": None,
            "agrupador_ferramenta": None,
        },
    )
    params = repo.execute_returning_one.call_args.args[1]
    assert params[0] is None


def test_update_persists_codigo_processo_change():
    """Observed case: PROC-0001 → PROC-0071 must actually persist."""
    svc = ProcessWriteService()
    body = _body(codigo_processo="PROC-0071")
    updated = {
        "processo_id": "p1",
        "codigo_processo": "PROC-0071",
        "nome_processo": "Processo X",
        "status_processo": "ativo",
    }
    with patch(
        "tm_app.application.services.process_write_service.ProcessoRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.update.return_value = updated
        repo.get.return_value = updated
        row = svc.update("p1", body, save_escopo=lambda *_a, **_k: None)
    assert row["codigo_processo"] == "PROC-0071"
    payload = repo.update.call_args.args[1]
    assert payload["codigo_processo"] == "PROC-0071"


def test_update_omitted_codigo_forwards_none_for_coalesce_preserve():
    svc = ProcessWriteService()
    body = _body(nome_processo="Renomeado")
    assert body.codigo_processo is None
    updated = {
        "processo_id": "p1",
        "codigo_processo": "PROC-0001",
        "nome_processo": "Renomeado",
        "status_processo": "ativo",
    }
    with patch(
        "tm_app.application.services.process_write_service.ProcessoRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.update.return_value = updated
        repo.get.return_value = updated
        row = svc.update("p1", body, save_escopo=lambda *_a, **_k: None)
    assert row["codigo_processo"] == "PROC-0001"
    payload = repo.update.call_args.args[1]
    assert payload["codigo_processo"] is None


def test_update_duplicate_codigo_maps_to_process_write_error():
    svc = ProcessWriteService()
    body = _body(codigo_processo="PROC-0071")
    with patch(
        "tm_app.application.services.process_write_service.ProcessoRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        repo.update.side_effect = PluginsRepositoryError(
            'Falha ao gravar registro: duplicate key value violates unique constraint '
            '"uq_processos_codigo" DETAIL: Key (codigo_processo)=(PROC-0071) already exists.'
        )
        with pytest.raises(ProcessWriteError) as exc:
            svc.update("p1", body, save_escopo=lambda *_a, **_k: None)
    assert "PROC-0071" in str(exc.value)
    assert "já existe" in str(exc.value).lower()


def test_gpt_update_process_persists_codigo_change():
    dispatch = GptActionsDispatchService()
    request = MagicMock()
    request.state.user = SimpleNamespace(id="u1", permissions=[], is_superadmin=True)
    updated = {
        "processo_id": "p1",
        "codigo_processo": "PROC-0071",
        "nome_processo": "X",
        "status_processo": "ativo",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_view_access",
            return_value=None,
        ),
        patch.object(dispatch, "_validate_processo_escopo_access", return_value=None),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessWriteService"
        ) as svc_cls,
    ):
        svc_cls.return_value.update.return_value = updated
        result, message = dispatch.update_record(
            request,
            "process",
            "p1",
            {
                "data": {
                    "nome_processo": "X",
                    "status_processo": "ativo",
                    "codigo_processo": "PROC-0071",
                }
            },
        )
    assert result["codigo_processo"] == "PROC-0071"
    assert "atualizado" in message.lower()
    svc_cls.return_value.update.assert_called_once()


def test_gpt_update_process_duplicate_codigo_is_400():
    dispatch = GptActionsDispatchService()
    request = MagicMock()
    request.state.user = SimpleNamespace(id="u1", permissions=[], is_superadmin=True)
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_processo_view_access",
            return_value=None,
        ),
        patch.object(dispatch, "_validate_processo_escopo_access", return_value=None),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessWriteService"
        ) as svc_cls,
    ):
        svc_cls.return_value.update.side_effect = ProcessWriteError(
            "Já existe um processo com o código PROC-0071."
        )
        with pytest.raises(GptActionsError) as exc:
            dispatch.update_record(
                request,
                "process",
                "p1",
                {
                    "data": {
                        "nome_processo": "X",
                        "status_processo": "ativo",
                        "codigo_processo": "PROC-0071",
                    }
                },
            )
    assert exc.value.status_code == 400
    assert "PROC-0071" in exc.value.message


def test_create_still_forwards_codigo_processo():
    body = SimpleNamespace(
        nome_processo="Novo",
        status_processo="ativo",
        descricao_processo=None,
        gestor_responsavel=None,
        objetivo_processo=None,
        codigo_processo="PROC-0099",
        familia_processo=None,
        agrupador_ferramenta=None,
        filial_id=None,
        setor_id=None,
    )
    payload = process_master_payload(body)
    assert payload["codigo_processo"] == "PROC-0099"


def test_schema_description_marks_codigo_mutable():
    field = ProcessoUpdateBody.model_fields["codigo_processo"]
    desc = (field.description or "").lower()
    assert "mutable" in desc
    assert "processo_id" in desc
