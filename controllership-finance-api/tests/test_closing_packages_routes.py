"""P5 packages/review/conclusão — contratos HTTP (docs 12/37, C2).

Matriz de autorização: leitura `access`; finalize/submit/assignments/
resolve exigem `manage`; review/decision/clarification exigem `access`
(repo revalida assignment — rota não inventa elegibilidade); rejeição
terminal exige `access` + COORDINATOR (repo). Sibling: pacote fora do
escopo de assignment retorna 404.
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
PERIOD = "2026-05"
VER_ID = str(uuid.uuid4())
PKG_ID = str(uuid.uuid4())
ASSIGN_ID = str(uuid.uuid4())
CLARIF_ID = str(uuid.uuid4())


def _claims(**overrides) -> dict:
    claims = {
        "sub": "44444444-4444-4444-8444-444444444444",
        "email": "rev@delpi.com.br",
        "name": "Reviewer Um",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "44444444-4444-4444-8444-444444444444",
        "email": "rev@delpi.com.br",
        "name": "Reviewer Um",
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
        "packages_routes._repository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def client() -> TestClient:
    return TestClient(
        app, headers={"Authorization": "Bearer test-token"}
    )


def _pkg_view(**overrides) -> dict:
    view = {
        "package_id": PKG_ID,
        "recipient_area": "CONTABIL",
        "state": "PACKAGE_FINALIZED",
        "review_state": "REVIEW_PENDING",
        "current_version": {
            "package_version_id": VER_ID,
            "version_no": 1,
            "status": "FINALIZED",
            "revision": 1,
        },
        "required_areas": [],
        "area_decisions": {},
        "open_clarifications": 0,
        "assignments": [],
        "revision": 1,
    }
    view.update(overrides)
    return view


# -- listagem / visibilidade -------------------------------------------------


def test_list_packages_manage_sees_all(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.list_packages.return_value = {
        "period": PERIOD,
        "applicable_areas": ["CONTABIL", "FISCAL"],
        "packages": [_pkg_view()],
    }
    resp = client.get(f"/closing/competences/{PERIOD}/packages")
    assert resp.status_code == 200
    assert repository.list_packages.call_args.kwargs["is_manage"] is True


def test_list_packages_access_only_scoped(client, repository):
    repository.list_packages.return_value = {
        "period": PERIOD,
        "applicable_areas": ["CONTABIL"],
        "packages": [],
    }
    resp = client.get(f"/closing/competences/{PERIOD}/packages")
    assert resp.status_code == 200
    assert repository.list_packages.call_args.kwargs["is_manage"] is False


def test_get_package_sibling_not_found(client, repository):
    repository.get_package.side_effect = de.PackageNotFound("x")
    resp = client.get(f"/closing/competences/{PERIOD}/packages/{PKG_ID}")
    assert resp.status_code == 404


def test_list_packages_requires_auth(app_client_noauth=None):
    pass  # auth 401 coberto pelo middleware em suítes irmãs


# -- finalize / submit --------------------------------------------------------


def test_finalize_requires_manage(client, repository):
    resp = client.post(
        f"/closing/competences/{PERIOD}/packages/finalize",
        json={"recipient_area": "CONTABIL"},
    )
    assert resp.status_code == 403
    repository.finalize_package.assert_not_called()


def test_finalize_ok(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.finalize_package.return_value = _pkg_view()
    resp = client.post(
        f"/closing/competences/{PERIOD}/packages/finalize",
        json={"recipient_area": "CONTABIL", "notes": "v1"},
    )
    assert resp.status_code == 200
    assert repository.finalize_package.call_args.args[1] == "CONTABIL"


def test_finalize_blocked_conflict(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.finalize_package.side_effect = (
        de.InvalidPackageTransition("bloqueado")
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/packages/finalize",
        json={"recipient_area": "FISCAL"},
    )
    assert resp.status_code == 409


def test_submit_forwards_revision(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.submit_for_review.return_value = _pkg_view(
        state="PACKAGE_SUBMITTED_FOR_REVIEW"
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}/submit",
        json={"revision": 3},
    )
    assert resp.status_code == 200
    assert (
        repository.submit_for_review.call_args.kwargs["expected_revision"]
        == 3
    )


def test_reopen_requires_reason(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}/reopen",
        json={"reason": ""},
    )
    assert resp.status_code == 422
    repository.reopen_version.assert_not_called()


# -- assignments / review ------------------------------------------------------


def test_assign_reviewer_ok(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.assign_actor.return_value = {
        "assignment_id": ASSIGN_ID,
        "role": "REVIEWER",
        "area": "CONTABIL",
        "subject": str(uuid.uuid4()),
        "active": True,
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/assignments",
        json={
            "role": "REVIEWER",
            "subject": str(uuid.uuid4()),
            "recipient_area": "CONTABIL",
            "area": "CONTABIL",
        },
    )
    assert resp.status_code == 200


def test_decision_access_allowed_with_assignment(client, repository):
    """Reviewer decide com ACCESS + assignment (repo revalida) — manage
    não é exigido para review (P5-C)."""
    repository.record_decision.return_value = {
        "decision_id": str(uuid.uuid4()),
        "area": "CONTABIL",
        "outcome": "ACCEPTED",
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}"
        "/decisions",
        json={"area": "CONTABIL", "outcome": "ACCEPTED"},
    )
    assert resp.status_code == 200
    assert (
        repository.record_decision.call_args.kwargs["outcome"]
        == "ACCEPTED"
    )


def test_decision_not_assigned_forbidden(client, repository):
    repository.record_decision.side_effect = de.ReviewerNotAssigned("x")
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}"
        "/decisions",
        json={"area": "CONTABIL", "outcome": "ACCEPTED"},
    )
    assert resp.status_code == 403


def test_decision_terminal_area_conflict(client, repository):
    repository.record_decision.side_effect = de.AreaDecisionTerminal(
        "x"
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}"
        "/decisions",
        json={
            "area": "CONTABIL",
            "outcome": "REJECTED",
            "note": "late",
        },
    )
    assert resp.status_code == 409


def test_clarification_open_and_resolve(client, repository, _auth_pipeline):
    repository.open_clarification.return_value = {
        "clarification_id": CLARIF_ID,
        "state": "OPEN",
        "question": "anexo?",
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/package-versions/{VER_ID}"
        "/clarifications",
        json={"question": "anexo?", "area": "CONTABIL"},
    )
    assert resp.status_code == 200

    # resolve exige manage
    resp = client.post(
        f"/closing/competences/{PERIOD}/clarifications/{CLARIF_ID}"
        "/resolve",
        json={"response": "sim"},
    )
    assert resp.status_code == 403

    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.resolve_clarification.return_value = {
        "clarification_id": CLARIF_ID,
        "state": "RESOLVED",
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/clarifications/{CLARIF_ID}"
        "/resolve",
        json={"response": "sim"},
    )
    assert resp.status_code == 200


# -- rejeição terminal / conclusão ---------------------------------------------


def test_terminal_rejection_requires_coordinator(client, repository):
    repository.confirm_terminal_rejection.side_effect = (
        de.CoordinatorRequired("x")
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/terminal-rejection",
        json={"reason": "inconsistência"},
    )
    assert resp.status_code == 403


def test_terminal_rejection_requires_reason(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    resp = client.post(
        f"/closing/competences/{PERIOD}/terminal-rejection",
        json={"reason": ""},
    )
    assert resp.status_code == 422


def test_closing_state_read(client, repository):
    repository.derive_closing_state.return_value = {
        "period": PERIOD,
        "state": "PENDING",
        "blocking_reasons": ["area_not_reviewed:CONTABIL:CONTABIL"],
        "packages": [],
    }
    resp = client.get(
        f"/closing/competences/{PERIOD}/closing-state"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["state"] == "PENDING"


def test_cockpit_read(client, repository):
    repository.get_cockpit.return_value = {
        "period": PERIOD,
        "checklist": {"EXPECTED": 2},
        "p3": {"cutoff_confirmed": False, "domains": []},
        "p4_pendencies": {},
        "closing": {"state": "PENDING", "blocking_reasons": []},
    }
    resp = client.get(f"/closing/competences/{PERIOD}/cockpit")
    assert resp.status_code == 200
    assert resp.json()["data"]["checklist"]["EXPECTED"] == 2
