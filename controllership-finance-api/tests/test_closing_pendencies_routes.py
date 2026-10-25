"""P4 pendências — contratos HTTP (doc 11 + RQ-P4-01..08).

Leitura/criação/claim/transições exigem `access` efetivo; reassign e
confirmação de classificação são decisões governadas → `manage`.
Sugestão determinística/IA nunca decide: só `confirmed_classification`
humano fecha a classificação. DISMISSED exige justificativa; estados
terminais não admitem mutação.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
PERIOD = "2026-04"
PENDENCY_ID = str(uuid.uuid4())


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
        fa,
        "request_has_valid_internal_service_token",
        lambda request: False,
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
        "pendencies_routes._repository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def client() -> TestClient:
    return TestClient(
        app, headers={"Authorization": "Bearer test-token"}
    )


def _pendency(**overrides) -> dict:
    pendency = {
        "pendency_id": PENDENCY_ID,
        "state": "OPEN",
        "kind": "MISSING_EVIDENCE",
        "revision": 1,
        "responsible_subject": None,
        "confirmed_classification": None,
    }
    pendency.update(overrides)
    return pendency


# -- leitura ------------------------------------------------------------


def test_list_pendencies_requires_authentication():
    anonymous = TestClient(app)
    resp = anonymous.get(
        f"/closing/competences/{PERIOD}/pendencies"
    )
    assert resp.status_code in (401, 403)


def test_list_pendencies_ok(client, repository):
    repository.list_pendencies.return_value = {
        "items": [_pendency()],
        "limit": 50,
        "offset": 0,
    }
    resp = client.get(f"/closing/competences/{PERIOD}/pendencies")
    assert resp.status_code == 200
    repository.list_pendencies.assert_called_once()
    kwargs = repository.list_pendencies.call_args.kwargs
    assert kwargs["request_scope"] == "BOTH"


def test_get_pendency_ok(client, repository):
    repository.get_pendency.return_value = _pendency()
    resp = client.get(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}"
    )
    assert resp.status_code == 200


def test_get_pendency_not_found(client, repository):
    repository.get_pendency.side_effect = de.PendencyNotFound(
        "Pendência não encontrada."
    )
    resp = client.get(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}"
    )
    assert resp.status_code == 404


def test_list_history_ok(client, repository):
    repository.list_pendency_history.return_value = {
        "pendency": _pendency(),
        "events": [],
    }
    resp = client.get(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}/history"
    )
    assert resp.status_code == 200


# -- criação -------------------------------------------------------------


def test_create_pendency_access_only(client, repository, _auth_pipeline):
    repository.create_pendency.return_value = _pendency()
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies",
        json={"kind": "OTHER", "title": "Pendência manual"},
    )
    assert resp.status_code == 201
    kwargs = repository.create_pendency.call_args.kwargs
    assert kwargs["kind"] == "OTHER"
    assert kwargs["title"] == "Pendência manual"


def test_create_pendency_with_suggestion(client, repository):
    """Sugestão determinística/IA é só recomendação — nunca decisão."""
    repository.create_pendency.return_value = _pendency(
        suggested_classification="RECONCILIATION",
        suggestion_source="DETERMINISTIC",
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies",
        json={
            "kind": "RECONCILIATION_DIVERGENCE",
            "title": "Divergência P7",
            "suggested_classification": "RECONCILIATION",
            "suggestion_source": "DETERMINISTIC",
            "suggestion_rationale": "mesmo item diverge há 2 dias",
        },
    )
    assert resp.status_code == 201
    kwargs = repository.create_pendency.call_args.kwargs
    assert kwargs["suggestion_source"] == "DETERMINISTIC"


def test_create_pendency_invalid_kind(client, repository):
    repository.create_pendency.side_effect = de.InvalidPendencyKind(
        "kind deve ser um de [...]."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies",
        json={"kind": "WHATEVER", "title": "x"},
    )
    assert resp.status_code == 422


# -- claim / reassign ----------------------------------------------------


def test_claim_pendency_access_only(client, repository):
    repository.claim_pendency.return_value = _pendency(
        state="IN_ANALYSIS",
        responsible_subject="33333333-3333-4333-8333-333333333333",
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}/claim",
        json={"revision": 1},
    )
    assert resp.status_code == 200
    kwargs = repository.claim_pendency.call_args
    assert kwargs.kwargs["expected_revision"] == 1


def test_claim_terminal_forbidden(client, repository):
    repository.claim_pendency.side_effect = de.PendencyTerminal(
        "Pendência terminal não admite claim."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}/claim",
        json={"revision": 1},
    )
    assert resp.status_code == 409


def test_reassign_requires_manage(client, repository, _auth_pipeline):
    """Reassign é decisão governada: `access` sozinho não basta."""
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}/reassign",
        json={"new_responsible": "user-x", "revision": 1},
    )
    assert resp.status_code == 403
    repository.reassign_pendency.assert_not_called()


def test_reassign_manage_ok(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.reassign_pendency.return_value = _pendency(
        responsible_subject="user-x"
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/{PENDENCY_ID}/reassign",
        json={"new_responsible": "user-x", "revision": 1},
    )
    assert resp.status_code == 200
    kwargs = repository.reassign_pendency.call_args.kwargs
    assert kwargs["new_responsible"] == "user-x"


# -- transições ----------------------------------------------------------


def test_transition_start_analysis(client, repository):
    repository.transition_pendency.return_value = _pendency(
        state="IN_ANALYSIS"
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/transition",
        json={"to_state": "IN_ANALYSIS", "revision": 1},
    )
    assert resp.status_code == 200


def test_transition_dismissed_needs_justification(client, repository):
    repository.transition_pendency.side_effect = (
        de.MissingDismissJustification(
            "DISMISSED exige justificativa."
        )
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/transition",
        json={"to_state": "DISMISSED", "revision": 1},
    )
    assert resp.status_code == 422


def test_transition_invalid_state(client, repository):
    repository.transition_pendency.side_effect = de.InvalidPendencyState(
        "to_state deve ser um de [...]."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/transition",
        json={"to_state": "CLOSED", "revision": 1},
    )
    assert resp.status_code == 422


def test_transition_terminal_forbidden(client, repository):
    repository.transition_pendency.side_effect = de.PendencyTerminal(
        "Pendência terminal não admite transição."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/transition",
        json={"to_state": "OPEN", "revision": 1},
    )
    assert resp.status_code == 409


def test_transition_stale_revision(client, repository):
    repository.transition_pendency.side_effect = de.StaleRevision(
        "A pendência foi alterada por outra sessão."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/transition",
        json={"to_state": "IN_ANALYSIS", "revision": 2},
    )
    assert resp.status_code == 409


# -- classificação -------------------------------------------------------


def test_confirm_classification_requires_manage(client, repository):
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/classification",
        json={"classification": "RECONCILIATION", "revision": 1},
    )
    assert resp.status_code == 403
    repository.confirm_classification.assert_not_called()


def test_confirm_classification_manage_ok(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.confirm_classification.return_value = _pendency(
        confirmed_classification="RECONCILIATION"
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/classification",
        json={
            "classification": "RECONCILIATION",
            "reason": "regra revisada pelo responsável",
            "revision": 1,
        },
    )
    assert resp.status_code == 200
    kwargs = repository.confirm_classification.call_args.kwargs
    assert kwargs["classification"] == "RECONCILIATION"


def test_confirm_classification_already_confirmed(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.confirm_classification.side_effect = (
        de.ClassificationAlreadyConfirmed(
            "Classificação já confirmada."
        )
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/pendencies/"
        f"{PENDENCY_ID}/classification",
        json={"classification": "OTHER", "revision": 1},
    )
    assert resp.status_code == 409
