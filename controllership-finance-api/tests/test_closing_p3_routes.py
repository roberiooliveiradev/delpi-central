"""P3 cutoff/conciliação — contratos HTTP (doc 10/15.1 + RQ-P3-01..08).

Leitura da readiness exige `access`; cutoff, revalidação e registro de
sources exigem `manage` efetivo. Divergência tolerada = exatamente
R$ 0,00; `STOCK_CLOSED` só reflete estado canônico do owner — nenhuma
rota o escreve.
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
        "p3_routes._repository",
        lambda: fake,
    )
    return fake


@pytest.fixture
def client() -> TestClient:
    return TestClient(
        app, headers={"Authorization": "Bearer test-token"}
    )


def _p3_state(**overrides) -> dict:
    state = {
        "period": PERIOD,
        "state": "WAITING_FOR_CUTOFF",
        "canonical_stock_state": "UNAVAILABLE",
        "cutoff": None,
        "reconciliations": [],
        "last_revalidation": None,
        "revalidation_valid": False,
        "blockers": ["cutoff_not_confirmed"],
    }
    state.update(overrides)
    return state


# -- leitura -------------------------------------------------------------


def test_get_p3_state_ok(client, repository):
    repository.get_p3_state.return_value = _p3_state()
    resp = client.get(f"/closing/competences/{PERIOD}/p3")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["state"] == "WAITING_FOR_CUTOFF"


def test_get_p3_state_not_opened(client, repository):
    repository.get_p3_state.side_effect = de.CompetenceNotOpened(
        "Competência não está aberta."
    )
    resp = client.get(f"/closing/competences/{PERIOD}/p3")
    assert resp.status_code == 404


def test_list_p3_events_ok(client, repository):
    repository.list_p3_events.return_value = {
        "items": [],
        "limit": 50,
        "offset": 0,
    }
    resp = client.get(f"/closing/competences/{PERIOD}/p3/events")
    assert resp.status_code == 200


# -- cutoff --------------------------------------------------------------


def test_confirm_cutoff_requires_manage(client, repository):
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/cutoff", json={}
    )
    assert resp.status_code == 403
    repository.confirm_cutoff.assert_not_called()


def test_confirm_cutoff_manage_ok(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.confirm_cutoff.return_value = {
        "cutoff_id": str(uuid.uuid4()),
        "confirmed_by": "ana",
        "confirmed_at": "2026-04-10T12:00:00+00:00",
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/cutoff",
        json={"notes": "fechamento físico conferido"},
    )
    assert resp.status_code == 201
    kwargs = repository.confirm_cutoff.call_args.kwargs
    assert kwargs["notes"] == "fechamento físico conferido"


def test_confirm_cutoff_twice_conflict(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.confirm_cutoff.side_effect = de.CutoffAlreadyConfirmed(
        "Cutoff já confirmado para esta competência."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/cutoff", json={}
    )
    assert resp.status_code == 409


# -- conciliação ---------------------------------------------------------


def test_upsert_reconciliation_requires_manage(client, repository):
    resp = client.put(
        f"/closing/competences/{PERIOD}/p3/reconciliations/P7",
        json={"source_state": "AVAILABLE"},
    )
    assert resp.status_code == 403
    repository.upsert_reconciliation.assert_not_called()


def test_upsert_reconciliation_manage_ok(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.upsert_reconciliation.return_value = {
        "reconciliation_id": str(uuid.uuid4()),
        "domain": "P7",
        "source_state": "AVAILABLE",
        "expected_amount": "100.00",
        "reported_amount": "100.00",
    }
    resp = client.put(
        f"/closing/competences/{PERIOD}/p3/reconciliations/P7",
        json={
            "source_state": "AVAILABLE",
            "expected_amount": "100.00",
            "reported_amount": "100.00",
            "provenance": {"source": "manual_confirmed",
                          "owner": "controladoria"},
        },
    )
    assert resp.status_code == 200
    call = repository.upsert_reconciliation.call_args
    assert call.args[1] == "P7"
    assert call.kwargs["provenance"]["source"] == "manual_confirmed"


def test_upsert_reconciliation_unknown_domain_404(
    client, repository, _auth_pipeline
):
    """Domínio fora do catálogo canônico não atinge o repositório."""
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    resp = client.put(
        f"/closing/competences/{PERIOD}/p3/reconciliations/BOGUS",
        json={"source_state": "AVAILABLE"},
    )
    assert resp.status_code in (404, 422)
    repository.upsert_reconciliation.assert_not_called()


def test_upsert_reconciliation_unavailable_source(
    client, repository, _auth_pipeline
):
    """Indisponibilidade honesta é estado válido — nunca vira zero."""
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.upsert_reconciliation.return_value = {
        "reconciliation_id": str(uuid.uuid4()),
        "domain": "H02",
        "source_state": "UNAVAILABLE",
    }
    resp = client.put(
        f"/closing/competences/{PERIOD}/p3/reconciliations/H02",
        json={"source_state": "UNAVAILABLE"},
    )
    assert resp.status_code == 200
    kwargs = repository.upsert_reconciliation.call_args.kwargs
    assert kwargs["source_state"] == "UNAVAILABLE"


# -- revalidação ---------------------------------------------------------


def test_revalidate_requires_manage(client, repository):
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/revalidations", json={}
    )
    assert resp.status_code == 403
    repository.revalidate.assert_not_called()


def test_revalidate_before_cutoff_conflict(
    client, repository, _auth_pipeline
):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.revalidate.side_effect = de.CutoffNotConfirmed(
        "Revalidação exige cutoff confirmado."
    )
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/revalidations", json={}
    )
    assert resp.status_code == 409


def test_revalidate_ok(client, repository, _auth_pipeline):
    _auth_pipeline["rbac"]["permissions"] = [ACCESS, MANAGE]
    repository.revalidate.return_value = {
        "revalidation_id": str(uuid.uuid4()),
        "result": "VALID",
        "input_fingerprint": "abc123",
    }
    resp = client.post(
        f"/closing/competences/{PERIOD}/p3/revalidations",
        json={"notes": "recontagem pós-cutoff"},
    )
    assert resp.status_code == 201
    body = resp.json()["data"]["revalidation"]
    assert body["result"] == "VALID"
