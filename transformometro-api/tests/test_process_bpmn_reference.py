"""G5 — processo ↔ BPMN Modeler: contrato da referência explícita.

Provam: vínculo explícito por (model_id, revision_number), write fail-closed,
read degradado, nenhum auto-follow-latest e nenhum bypass de ownership.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.ports.bpmn_modeler_port import BpmnLookupResult
from tm_app.application.use_cases.manage_process_bpmn_reference import (
    BpmnDependencyUnavailable,
    ProcessBpmnReferenceUseCases,
)
from tm_app.domain.entities.process_bpmn_reference import ProcessBpmnReference

PROCESSO = "33333333-3333-3333-3333-333333333333"
MODEL_A = "aaaaaaaa-1111-1111-1111-111111111111"
MODEL_B = "bbbbbbbb-2222-2222-2222-222222222222"
AUTH = "Bearer test-token"
USER = SimpleNamespace(id="user-a", sub="user-a", is_superadmin=True, permissions=[])


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[str, ProcessBpmnReference] = {}
        self.exists = True

    def process_exists(self, processo_id: str) -> bool:
        return self.exists

    def get_active(self, processo_id: str):
        return self.rows.get(processo_id)

    def upsert(self, *, processo_id, bpmn_model_id, bpmn_revision_number, actor_user_id):
        previous = self.rows.get(processo_id)
        ref = ProcessBpmnReference(
            id="ref-1",
            processo_id=processo_id,
            bpmn_model_id=bpmn_model_id,
            bpmn_revision_number=bpmn_revision_number,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.rows[processo_id] = ref
        return ref, previous

    def soft_delete(self, *, processo_id, actor_user_id):
        return self.rows.pop(processo_id, None)


class FakeBpmn:
    """Stub do port remoto — registra chamadas e serve payloads fixos."""

    def __init__(self, models=None, revisions=None, state="ok") -> None:
        self.models = models or {}
        self.revisions = revisions or {}
        self.state = state
        self.calls: list[tuple] = []

    def _result(self, payload):
        if self.state != "ok":
            return BpmnLookupResult(self.state)
        return BpmnLookupResult("ok", payload) if payload is not None else BpmnLookupResult("not_found")

    def list_models(self, *, authorization):
        self.calls.append(("list_models", authorization))
        if self.state != "ok":
            return BpmnLookupResult(self.state)
        return BpmnLookupResult("ok", {"data": {"items": list(self.models.values())}})

    def get_model(self, *, authorization, model_id):
        self.calls.append(("get_model", model_id, authorization))
        return self._result(self.models.get(model_id))

    def list_revisions(self, *, authorization, model_id):
        self.calls.append(("list_revisions", model_id, authorization))
        return self._result({"data": {"items": self.revisions.get(model_id, [])}})

    def get_revision(self, *, authorization, model_id, revision_number):
        self.calls.append(("get_revision", model_id, revision_number, authorization))
        return self._result(
            self.revisions.get(model_id, {}).get(revision_number)
            if isinstance(self.revisions.get(model_id), dict)
            else None
        )


def _model(model_id=MODEL_A, latest=1):
    return {
        "id": model_id,
        "display_name": "Processo X",
        "latest_revision_number": latest,
        "archived_at": None,
        "version": 7,  # concurrency token — NÃO é revision_number
    }


def _revision(n=1):
    return {
        "revision_number": n,
        "revision_id": f"rev-{n}",
        "name": f"R{n}",
        "artifact_sha256": "abc123",
        "origin": "manual",
        "created_at": "2025-01-01T00:00:00Z",
        "created_by_name": "User A",
    }


def _uc(repo=None, bpmn=None):
    return ProcessBpmnReferenceUseCases(repo or FakeRepo(), bpmn or FakeBpmn())


def test_get_reference_empty():
    uc = _uc(repo=FakeRepo(), bpmn=FakeBpmn())
    result = uc.get_reference(USER, PROCESSO, authorization=AUTH)
    assert result["reference"] is None
    assert result["resolved"] is None


def test_set_reference_persists_identity_only():
    bpmn = FakeBpmn(models={MODEL_A: _model()}, revisions={MODEL_A: {1: _revision(1)}})
    repo = FakeRepo()
    uc = _uc(repo=repo, bpmn=bpmn)

    result = uc.set_reference(
        USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH
    )
    assert result["reference"]["model_id"] == MODEL_A
    assert result["reference"]["revision_number"] == 1
    assert result["previous"] is None
    assert result["resolved"]["state"] == "resolved"
    assert result["resolved"]["artifact_sha256"] == "abc123"
    # nada de XML/artefacto persistido
    stored = repo.get_active(PROCESSO)
    assert stored.bpmn_model_id == MODEL_A
    assert stored.bpmn_revision_number == 1


def test_set_reference_model_without_revision_denied():
    bpmn = FakeBpmn(models={MODEL_A: _model(latest=None)})
    uc = _uc(repo=FakeRepo(), bpmn=bpmn)
    with pytest.raises(ValueError, match="não possui uma revisão"):
        uc.set_reference(
            USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH
        )


def test_set_reference_missing_revision_denied():
    bpmn = FakeBpmn(models={MODEL_A: _model(latest=5)}, revisions={MODEL_A: {}})
    uc = _uc(repo=FakeRepo(), bpmn=bpmn)
    with pytest.raises(LookupError):
        uc.set_reference(
            USER, PROCESSO, model_id=MODEL_A, revision_number=999, authorization=AUTH
        )


def test_set_reference_foreign_model_denied_without_leak():
    """Modelo de outro owner → Modeler 404 → link negado, sem existence leak."""
    bpmn = FakeBpmn(models={})  # modelo inacessível para este usuário
    uc = _uc(repo=FakeRepo(), bpmn=bpmn)
    with pytest.raises(LookupError, match="não encontrado ou sem acesso"):
        uc.set_reference(
            USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH
        )


def test_set_reference_modeler_unavailable_fails_closed():
    repo = FakeRepo()
    bpmn = FakeBpmn(state="unavailable")
    uc = _uc(repo=repo, bpmn=bpmn)
    with pytest.raises(BpmnDependencyUnavailable):
        uc.set_reference(
            USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH
        )
    assert repo.get_active(PROCESSO) is None  # nenhum dangling reference


def test_read_survives_modeler_unavailable():
    repo = FakeRepo()
    bpmn = FakeBpmn(models={MODEL_A: _model()}, revisions={MODEL_A: {1: _revision(1)}})
    uc = _uc(repo=repo, bpmn=bpmn)
    uc.set_reference(USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH)

    degraded = _uc(repo=repo, bpmn=FakeBpmn(state="unavailable"))
    result = degraded.get_reference(USER, PROCESSO, authorization=AUTH)
    assert result["reference"]["model_id"] == MODEL_A  # referência preservada
    assert result["resolved"]["state"] == "unavailable"


def test_no_auto_follow_latest():
    repo = FakeRepo()
    models = {MODEL_A: _model(latest=1)}
    revisions = {MODEL_A: {1: _revision(1)}}
    uc = _uc(repo=repo, bpmn=FakeBpmn(models=models, revisions=revisions))
    uc.set_reference(USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH)

    # Modeler ganha revisão 2 — referência continua R1
    models[MODEL_A] = _model(latest=2)
    revisions[MODEL_A][2] = _revision(2)
    result = uc.get_reference(USER, PROCESSO, authorization=AUTH)
    assert result["reference"]["revision_number"] == 1
    assert result["resolved"]["latest_revision_number"] == 2
    # badge read-only: nenhum write aconteceu
    assert repo.get_active(PROCESSO).bpmn_revision_number == 1


def test_explicit_revision_replace_and_model_switch():
    repo = FakeRepo()
    revisions = {MODEL_A: {1: _revision(1), 2: _revision(2)}, MODEL_B: {1: _revision(1)}}
    models = {MODEL_A: _model(latest=2), MODEL_B: _model(MODEL_B, latest=1)}
    uc = _uc(repo=repo, bpmn=FakeBpmn(models=models, revisions=revisions))

    uc.set_reference(USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH)
    result = uc.set_reference(
        USER, PROCESSO, model_id=MODEL_A, revision_number=2, authorization=AUTH
    )
    assert result["previous"]["revision_number"] == 1
    assert result["reference"]["revision_number"] == 2

    result = uc.set_reference(
        USER, PROCESSO, model_id=MODEL_B, revision_number=1, authorization=AUTH
    )
    assert result["previous"]["model_id"] == MODEL_A
    assert result["reference"]["model_id"] == MODEL_B


def test_remove_reference_only_touches_transformometro():
    repo = FakeRepo()
    bpmn = FakeBpmn(models={MODEL_A: _model()}, revisions={MODEL_A: {1: _revision(1)}})
    uc = _uc(repo=repo, bpmn=bpmn)
    uc.set_reference(USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH)

    calls_before = len(bpmn.calls)
    result = uc.remove_reference(USER, PROCESSO)
    assert result["removed"]["model_id"] == MODEL_A
    assert repo.get_active(PROCESSO) is None
    # unlink é Transformômetro-only: zero chamadas ao Modeler
    assert len(bpmn.calls) == calls_before


def test_remove_reference_when_none():
    uc = _uc(repo=FakeRepo(), bpmn=FakeBpmn())
    with pytest.raises(LookupError):
        uc.remove_reference(USER, PROCESSO)


def test_user_authorization_forwarded_to_modeler():
    bpmn = FakeBpmn(models={MODEL_A: _model()}, revisions={MODEL_A: {1: _revision(1)}})
    uc = _uc(repo=FakeRepo(), bpmn=bpmn)
    uc.set_reference(USER, PROCESSO, model_id=MODEL_A, revision_number=1, authorization=AUTH)
    for call in bpmn.calls:
        assert call[-1] == AUTH  # bearer do usuário, nunca service token


def test_list_revisions_picker():
    bpmn = FakeBpmn(
        models={MODEL_A: _model(latest=2)},
        revisions={MODEL_A: {1: _revision(1), 2: _revision(2)}},
    )
    # FakeBpmn.list_revisions espera lista; adaptar fixture
    bpmn.revisions = {MODEL_A: [_revision(1), _revision(2)]}
    uc = _uc(repo=FakeRepo(), bpmn=bpmn)
    result = uc.list_model_revisions(USER, PROCESSO, MODEL_A, authorization=AUTH)
    assert [i["revision_number"] for i in result["items"]] == [1, 2]


# -- HTTP level (envelope + auth wiring) -------------------------------------

def test_http_set_reference_envelope(tm_client):
    from tm_app.interface.http.routes import process_bpmn_reference_routes as mod

    fake = _uc(
        repo=FakeRepo(),
        bpmn=FakeBpmn(models={MODEL_A: _model()}, revisions={MODEL_A: {1: _revision(1)}}),
    )
    with patch.object(mod, "_use_cases", fake):
        resp = tm_client.put(
            f"/transformometro/processos/{PROCESSO}/bpmn-reference",
            json={"model_id": MODEL_A, "revision_number": 1},
            headers={"Authorization": AUTH},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["reference"]["model_id"] == MODEL_A
    assert data["resolved"]["state"] == "resolved"


def test_http_get_reference_empty(tm_client):
    from tm_app.interface.http.routes import process_bpmn_reference_routes as mod

    with patch.object(mod, "_use_cases", _uc()):
        resp = tm_client.get(
            f"/transformometro/processos/{PROCESSO}/bpmn-reference",
            headers={"Authorization": AUTH},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["reference"] is None


def test_http_invalid_revision_rejected(tm_client):
    from tm_app.interface.http.routes import process_bpmn_reference_routes as mod

    with patch.object(mod, "_use_cases", _uc()):
        resp = tm_client.put(
            f"/transformometro/processos/{PROCESSO}/bpmn-reference",
            json={"model_id": MODEL_A, "revision_number": 0},
            headers={"Authorization": AUTH},
        )
    assert resp.status_code in (400, 422)
