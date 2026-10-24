"""P2 validação humana — contratos HTTP (doc 09 + RQ-P2-02..12).

Validador V1 = `access` + `manage` efetivos; ações de item (N/A,
cancelamento, item excepcional, solicitação de correção) exigem apenas
`access`; revisão de correção e reversão exigem `manage`. Payloads de
rejeição exigem motivo estruturado do catálogo (`OTHER` exige
comentário); justificativa obrigatória nas transições governadas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
NOW = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)


def _claims(**overrides) -> dict:
    claims = {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: False
    )
    monkeypatch.setattr(
        fa, "validate_token", lambda token: _claims()
    )
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def repository(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "validations_routes._repository",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _headers() -> dict:
    return {"Authorization": f"Bearer {TOKEN}"}


def _grant_manage(rbac_holder):
    rbac_holder["rbac"] = _rbac(permissions=[ACCESS, MANAGE])


DOC_ID = str(uuid.uuid4())
ITEM_KEY = "CK-E-01"
DECISION_ID = str(uuid.uuid4())
CORRECTION_ID = str(uuid.uuid4())


# -- decisão por anexo (PER_ATTACHMENT) ---------------------------------------


def test_decide_version_accepted_201(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.decide_version.return_value = {
        "decision_id": uuid.uuid4(),
        "document_id": DOC_ID,
        "version_no": 1,
        "decision": "ACCEPTED",
        "reason_code": None,
        "comment": None,
        "item_state": "EXPECTED",
        "decided_by": "33333333-3333-4333-8333-333333333333",
        "created_at": NOW,
    }
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 201
    repository.decide_version.assert_called_once()


def test_decide_version_requires_manage(repository):
    """Access sozinho não valida — RQ-P2-03 (ACCESS != MANAGE)."""
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 403
    assert response.json()["data"]["error"]["code"] == "forbidden"
    repository.decide_version.assert_not_called()


def test_decide_version_reject_requires_reason(
    repository, _auth_pipeline
):
    _grant_manage(_auth_pipeline)
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "REJECTED"},
        headers=_headers(),
    )
    assert response.status_code == 422
    assert (
        response.json()["data"]["error"]["code"]
        == "invalid_rejection_reason"
    )


def test_decide_version_other_reason_requires_comment(
    repository, _auth_pipeline
):
    _grant_manage(_auth_pipeline)
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "REJECTED", "reason_code": "OTHER"},
        headers=_headers(),
    )
    assert response.status_code == 422
    assert (
        response.json()["data"]["error"]["code"] == "missing_justification"
    )


def test_decide_version_scope_mismatch_409(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.decide_version.side_effect = de.ValidationScopeMismatch(
        "Este item exige validação do conjunto inteiro."
    )
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"]
        == "validation_scope_mismatch"
    )


def test_decide_version_item_out_of_scope_404(
    repository, _auth_pipeline
):
    """Recurso fora do filial-contexto declarado = 404 sem vazamento."""
    _grant_manage(_auth_pipeline)
    repository.decide_version.side_effect = de.ItemNotFound(
        "Item do checklist não encontrado."
    )
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation"
        "?branch_scope=MATRIX",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 404
    repository.decide_version.assert_called_once()
    assert (
        repository.decide_version.call_args.kwargs["request_scope"]
        == "MATRIX"
    )


def test_decide_requires_bearer(repository):
    response = _client().post(
        f"/closing/competences/2026-05/documents/{DOC_ID}/validation",
        json={"decision": "ACCEPTED"},
    )
    assert response.status_code == 401


# -- decisão por conjunto (WHOLE_SET) ------------------------------------------


def test_decide_item_set_accepted_201(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.decide_item_set.return_value = {
        "decision_id": uuid.uuid4(),
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "scope": "WHOLE_SET",
        "composition": [],
        "decision": "ACCEPTED",
        "item_state": "ACCEPTED",
        "decided_by": "33333333-3333-4333-8333-333333333333",
        "created_at": NOW,
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/validation",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 201
    repository.decide_item_set.assert_called_once()


def test_decide_item_set_no_evidence_409(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.decide_item_set.side_effect = de.NoEvidence(
        "Não há evidência anexada para validar."
    )
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/validation",
        json={"decision": "ACCEPTED"},
        headers=_headers(),
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"] == "no_evidence"
    )


# -- reversão de rejeição --------------------------------------------------------


def test_reverse_rejection_201(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.reverse_decision.return_value = {
        "decision_id": uuid.uuid4(),
        "reversed_decision_id": DECISION_ID,
        "decision": "REVERSED",
        "result_state": "UNDER_REVIEW",
        "item_state": "EXPECTED",
        "decided_by": "33333333-3333-4333-8333-333333333333",
        "created_at": NOW,
    }
    response = _client().post(
        f"/closing/competences/2026-05/decisions/{DECISION_ID}/reverse",
        json={
            "result_state": "UNDER_REVIEW",
            "justification": "Análise revisada — legível.",
        },
        headers=_headers(),
    )
    assert response.status_code == 201


def test_reverse_blocked_by_newer_version(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.reverse_decision.side_effect = de.InvalidStateTransition(
        "Nova versão já anexada — reversão bloqueada."
    )
    response = _client().post(
        f"/closing/competences/2026-05/decisions/{DECISION_ID}/reverse",
        json={
            "result_state": "ACCEPTED",
            "justification": "revisão",
        },
        headers=_headers(),
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"]
        == "invalid_state_transition"
    )


def test_reverse_requires_same_validator(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.reverse_decision.side_effect = de.Forbidden(
        "Somente o validador que rejeitou pode reverter."
    )
    response = _client().post(
        f"/closing/competences/2026-05/decisions/{DECISION_ID}/reverse",
        json={
            "result_state": "ACCEPTED",
            "justification": "revisão",
        },
        headers=_headers(),
    )
    assert response.status_code == 403


# -- N/A -------------------------------------------------------------------------


def test_mark_na_conditional_200(repository):
    repository.mark_not_applicable.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "state": "NOT_APPLICABLE",
        "state_reason": "Sem movimentação na filial.",
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/not-applicable",
        json={"justification": "Sem movimentação na filial."},
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "NOT_APPLICABLE"


def test_mark_na_required_item_409(repository):
    repository.mark_not_applicable.side_effect = (
        de.InvalidStateTransition(
            "Item REQUIRED não admite marcação N/A — apenas CONDITIONAL."
        )
    )
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/not-applicable",
        json={"justification": "tentativa"},
        headers=_headers(),
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"]
        == "invalid_state_transition"
    )


def test_mark_na_missing_justification_422(repository):
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/not-applicable",
        json={},
        headers=_headers(),
    )
    assert response.status_code == 422


def test_revert_na_200(repository):
    repository.revert_not_applicable.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "state": "EXPECTED",
        "state_reason": "Voltou a ser exigido.",
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}"
        "/not-applicable/revert",
        json={"justification": "Voltou a ser exigido."},
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "EXPECTED"


# -- cancelamento de item ---------------------------------------------------------


def test_cancel_item_200(repository):
    repository.cancel_item.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "state": "CANCELLED",
        "state_reason": "Requisito revogado antes da execução.",
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/cancel",
        json={"justification": "Requisito revogado antes da execução."},
        headers=_headers(),
    )
    assert response.status_code == 200


def test_cancel_item_with_evidence_409(repository):
    repository.cancel_item.side_effect = de.ItemLocked(
        "Item já possui evidência — cancelamento simples bloqueado."
    )
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/cancel",
        json={"justification": "tentativa"},
        headers=_headers(),
    )
    assert response.status_code == 409
    assert response.json()["data"]["error"]["code"] == "item_locked"


# -- item excepcional --------------------------------------------------------------


def test_create_exceptional_item_201(repository):
    repository.create_exceptional_item.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": "EXC-17",
        "state": "EXPECTED",
        "exceptional": True,
        "name": "Extrato complementar",
        "sheet": "ELETRONICO",
        "origin_kind": "EXTERNAL",
        "recipient_area": "FISCAL",
        "applicability": "REQUIRED",
        "branch_scope": "BOTH",
        "validation_scope": "PER_ATTACHMENT",
    }
    response = _client().post(
        "/closing/competences/2026-05/items",
        json={
            "sheet": "ELETRONICO",
            "name": "Extrato complementar",
            "justification": "Requisito surgido na conferência.",
            "recipient_area": "FISCAL",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    assert response.json()["data"]["exceptional"] is True
    repository.create_exceptional_item.assert_called_once()
    assert (
        repository.create_exceptional_item.call_args.kwargs["origin_kind"]
        == "EXTERNAL"
    )


def test_create_exceptional_item_access_only(repository):
    """ACCESS basta — doc 09: 'ACCESS pode criar item apenas para a
    competência corrente'."""
    repository.create_exceptional_item.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": "EXC-17",
        "state": "EXPECTED",
        "exceptional": True,
    }
    response = _client().post(
        "/closing/competences/2026-05/items",
        json={
            "sheet": "ELETRONICO",
            "name": "Item excepcional",
            "justification": "motivo",
        },
        headers=_headers(),
    )
    assert response.status_code == 201


# -- correção estrutural ------------------------------------------------------------


def test_request_correction_201(repository):
    repository.request_correction.return_value = {
        "correction_id": uuid.uuid4(),
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "item_revision": 1,
        "changes": {"validation_scope": "WHOLE_SET"},
        "status": "PENDING",
        "requested_by": "33333333-3333-4333-8333-333333333333",
        "requested_at": NOW,
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections",
        json={
            "changes": {"validation_scope": "WHOLE_SET"},
            "justification": "Escopo errado na abertura.",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "PENDING"


def test_request_correction_unknown_field_422(repository):
    repository.request_correction.side_effect = de.InvalidUpload(
        "Campos não corrigíveis: state"
    )
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections",
        json={
            "changes": {"state": "ACCEPTED"},
            "justification": "tentativa",
        },
        headers=_headers(),
    )
    assert response.status_code == 422
    assert (
        response.json()["data"]["error"]["code"] == "invalid_upload"
    )


def test_review_correction_approve_200(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.review_correction.return_value = {
        "correction_id": CORRECTION_ID,
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "status": "APPROVED",
        "new_revision": 2,
        "reviewed_by": "33333333-3333-4333-8333-333333333333",
    }
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections"
        f"/{CORRECTION_ID}/review",
        json={"approve": True},
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["new_revision"] == 2


def test_review_correction_requires_manage(repository):
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections"
        f"/{CORRECTION_ID}/review",
        json={"approve": True},
        headers=_headers(),
    )
    assert response.status_code == 403
    repository.review_correction.assert_not_called()


def test_review_correction_stale_revision_409(repository, _auth_pipeline):
    _grant_manage(_auth_pipeline)
    repository.review_correction.side_effect = de.StaleRevision(
        "O item mudou desde a solicitação."
    )
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections"
        f"/{CORRECTION_ID}/review",
        json={"approve": True},
        headers=_headers(),
    )
    assert response.status_code == 409
    assert (
        response.json()["data"]["error"]["code"] == "stale_revision"
    )


def test_review_correction_reject_requires_reason(
    repository, _auth_pipeline
):
    _grant_manage(_auth_pipeline)
    response = _client().post(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections"
        f"/{CORRECTION_ID}/review",
        json={"approve": False},
        headers=_headers(),
    )
    assert response.status_code == 422
    assert (
        response.json()["data"]["error"]["code"]
        == "missing_justification"
    )


# -- leituras --------------------------------------------------------------------


def test_get_item_validation_200(repository):
    repository.list_item_decisions.return_value = {
        "snapshot_item_id": uuid.uuid4(),
        "item_key": ITEM_KEY,
        "state": "EXPECTED",
        "validation_scope": "PER_ATTACHMENT",
        "applicability": "REQUIRED",
        "documents": [],
        "decisions": [],
    }
    response = _client().get(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/validation",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["item_key"] == ITEM_KEY


def test_list_item_corrections_200(repository):
    repository.list_corrections.return_value = [
        {
            "correction_id": uuid.uuid4(),
            "item_key": ITEM_KEY,
            "status": "PENDING",
            "item_revision": 1,
            "changes": {},
            "requested_at": NOW,
        }
    ]
    response = _client().get(
        f"/closing/competences/2026-05/items/{ITEM_KEY}/corrections",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["corrections"]) == 1
