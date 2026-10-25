"""Matriz R01–R15 — contrato HTTP (B-δ, doc 93).

A matriz é agregação derivada do snapshot: itens por R-ID e estado de
validação + catálogo canônico de fonte/owner. Consultas operacionais
nunca viram relatório oficial; R-IDs sem contrato ficam explícitos.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
PERIOD = "2026-04"


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
def checklist_repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "reports_routes.ClosingChecklistRepository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def client() -> TestClient:
    return TestClient(
        app, headers={"Authorization": "Bearer test-token"}
    )


def _item(report_ref, state="EXPECTED", branch_scope="BOTH"):
    return {
        "snapshot_item_id": "s-1",
        "item_key": "CK-E-01",
        "totvs_report_ref": report_ref,
        "state": state,
        "branch_scope": branch_scope,
    }


def test_matrix_requires_authentication():
    anonymous = TestClient(app)
    resp = anonymous.get(f"/closing/competences/{PERIOD}/reports")
    assert resp.status_code in (401, 403)


def test_matrix_covers_all_15_report_ids(client, checklist_repo):
    checklist_repo.list_competence_items.return_value = []
    resp = client.get(f"/closing/competences/{PERIOD}/reports")
    assert resp.status_code == 200
    reports = resp.json()["data"]["reports"]
    ids = {r["report_id"] for r in reports}
    assert ids == {f"R{n:02d}" for n in range(1, 16)}


def test_matrix_counts_items_by_state(client, checklist_repo):
    checklist_repo.list_competence_items.return_value = [
        _item("R13", "ACCEPTED"),
        _item("R13", "EXPECTED"),
        _item("R13", "CANCELLED"),
        _item("R02", "ACCEPTED"),
    ]
    resp = client.get(f"/closing/competences/{PERIOD}/reports")
    reports = {
        r["report_id"]: r
        for r in resp.json()["data"]["reports"]
    }
    assert reports["R13"]["checklist_items"] == 3
    assert reports["R13"]["items_validated"] == 1
    assert reports["R13"]["items_terminal"] == 2
    assert reports["R13"]["items_pending"] == 1
    assert reports["R13"]["coverage"] == "partial"
    assert reports["R02"]["coverage"] == "validated"
    assert reports["R04"]["checklist_items"] == 0
    assert reports["R04"]["coverage"] == "pending"


def test_matrix_never_marks_operational_as_official(
    client, checklist_repo
):
    checklist_repo.list_competence_items.return_value = []
    resp = client.get(f"/closing/competences/{PERIOD}/reports")
    reports = {
        r["report_id"]: r
        for r in resp.json()["data"]["reports"]
    }
    assert reports["R01"]["source_kind"] == "OPERATIONAL_VIEW"
    assert reports["R03"]["source_kind"] == "OPERATIONAL_VIEW"
    assert "não é" in reports["R01"]["note"].lower()
    assert reports["R04"]["source_kind"] == "PENDING_CONTRACT"


def test_matrix_branch_scope_filter(client, checklist_repo):
    checklist_repo.list_competence_items.return_value = [
        _item("R13", "EXPECTED", "BRANCH"),
        _item("R02", "ACCEPTED", "MATRIX"),
    ]
    resp = client.get(
        f"/closing/competences/{PERIOD}/reports?branch_scope=MATRIX"
    )
    reports = {
        r["report_id"]: r
        for r in resp.json()["data"]["reports"]
    }
    # item BRANCH fica fora do contexto MATRIX; BOTH seria alcançável.
    assert reports["R13"]["checklist_items"] == 0
    assert reports["R02"]["checklist_items"] == 1


def test_matrix_not_opened(client, checklist_repo):
    checklist_repo.list_competence_items.side_effect = (
        de.CompetenceNotOpened("Competência não está aberta.")
    )
    resp = client.get(f"/closing/competences/{PERIOD}/reports")
    assert resp.status_code == 404
