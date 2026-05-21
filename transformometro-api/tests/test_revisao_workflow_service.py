from unittest.mock import MagicMock

import pytest

from tm_app.application.services.revisao_workflow_service import (
    RevisaoWorkflowError,
    RevisaoWorkflowService,
)


def _repo_with_status(status: str):
    repo = MagicMock()
    repo.get.return_value = {"revisao_id": "r1", "status_aprovacao": status}
    repo.set_status_aprovacao.return_value = {
        "revisao_id": "r1",
        "status_aprovacao": "em_analise",
    }
    return repo


def test_submeter_from_rascunho():
    repo = _repo_with_status("rascunho")
    svc = RevisaoWorkflowService(repo)
    row = svc.submeter("r1")
    assert row["status_aprovacao"] == "em_analise"
    repo.set_status_aprovacao.assert_called_once()


def test_submeter_from_rejeitada():
    repo = _repo_with_status("rejeitada")
    svc = RevisaoWorkflowService(repo)
    svc.submeter("r1")
    repo.set_status_aprovacao.assert_called_once_with(
        "r1", "em_analise", aprovado_por_email=None, motivo_rejeicao=None
    )


def test_submeter_blocked_from_em_analise():
    repo = _repo_with_status("em_analise")
    svc = RevisaoWorkflowService(repo)
    with pytest.raises(RevisaoWorkflowError, match="em_analise"):
        svc.submeter("r1")


def test_aprovar_requires_em_analise():
    repo = _repo_with_status("rascunho")
    svc = RevisaoWorkflowService(repo)
    with pytest.raises(RevisaoWorkflowError):
        svc.aprovar("r1", "a@b.com")


def test_rejeitar_requires_motivo():
    repo = _repo_with_status("em_analise")
    svc = RevisaoWorkflowService(repo)
    with pytest.raises(RevisaoWorkflowError, match="motivo"):
        svc.rejeitar("r1", "  ", "a@b.com")


def test_ensure_can_activate_only_aprovada():
    with pytest.raises(RevisaoWorkflowError, match="aprovadas"):
        RevisaoWorkflowService.ensure_can_activate({"status_aprovacao": "rascunho"})
    RevisaoWorkflowService.ensure_can_activate({"status_aprovacao": "aprovada"})
