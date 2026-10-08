"""P2 — ponte S2S: Production Control → Requests API (process-issue).

Cobre:
* POST /integrations/requests: service token, caller app, allowlist
  source/type, Idempotency-Key e requester externo;
* execute_external: mesmo motor de criação (número, status, outbox,
  idempotência) sem RBAC de solicitante;
* ProcessIssuePayloadValidator: contrato do snapshot do cockpit;
* notificações: fan-out por função + filial e silêncio do requester externo.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from requests_app.application.errors import ApplicationError
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    TransitionRequestUseCase,
)
from requests_app.domain.services.external_requester import (
    is_external_requester_id,
)
from requests_app.domain.services.process_issue_payload_validator import (
    ProcessIssuePayloadValidator,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_outbox_repository import (  # noqa: E501
    InMemoryIntegrationOutboxRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (  # noqa: E501
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)
from requests_app.interface.http.routes import integrations_routes

SERVICE_TOKEN = "s2s-test-token"
CALLER_HEADERS = {
    "X-Delpi-Service-Token": SERVICE_TOKEN,
    "X-Delpi-Caller-App": "production-control-api",
}


def _user(*, user_id: str, permissions: list[str]):
    return SimpleNamespace(id=user_id, name="Analista", permissions=permissions)


def _payload(**overrides):
    base = {
        "source": "operator_cockpit",
        "reportedAt": "2026-10-08T12:00:00+00:00",
        "issue": {
            "code": "tool_not_linked",
            "reportedToolCode": "F12345",
            "note": "Ferramenta não consta na operação.",
        },
        "operator": {"code": "001234", "name": "Maria Silva"},
        "operation": {
            "productionOrder": "24640401002",
            "operationCode": "03",
            "description": "MONTAGEM",
            "reportedWorkCenter": "CT-63",
            "workCenterName": "Montagem 03",
            "productCode": "10045678",
            "paProductCode": "90264238",
            "toolSnapshot": "",
            "plannedQty": 100,
        },
        "materialsSnapshotAvailable": True,
        "materials": [
            {
                "productCode": "10081234",
                "description": "TERMINAL FASTON",
                "unit": "PC",
                "originalQty": 500,
                "openQty": 120,
                "consumedQty": 380,
            }
        ],
    }
    base.update(overrides)
    return base


@pytest.fixture
def harness():
    process_issue = RequestTypeRegistry.from_workflow_content(
        code="process-issue",
        name="Problema de Processo",
        workflow_name="process_issue",
        permission_prefix="my-requests.process-issue",
        presentation_mode="schema_driven",
        branch_scope="required",
    )
    types = InMemoryRequestTypeRepository([process_issue])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    outbox = InMemoryIntegrationOutboxRepository()
    use_case = CreateRequestUseCase(types, requests, idem, outbox=outbox)
    return types, requests, idem, outbox, use_case


def _external(harness, **overrides):
    *_, use_case = harness
    kwargs = {
        "requester_id": "operator:02:12345",
        "requester_name": "Maria Silva",
        "type_code": "process-issue",
        "payload": _payload(),
        "branch_code": "02",
        "idempotency_key": str(uuid4()),
    }
    kwargs.update(overrides)
    return use_case.execute_external(**kwargs)


# --- use case: criação externa ------------------------------------------------


def test_external_create_persists_operator_identity(harness):
    created = _external(harness)
    assert created["status"] == "submitted"
    assert created["type_code"] == "process-issue"
    assert created["branch_code"] == "02"
    assert created["created_by_user_id"] == "operator:02:12345"
    assert created["created_by_name"] == "Maria Silva"
    assert created["request_number"]


def test_external_requester_must_use_external_scheme(harness):
    *_, use_case = harness
    with pytest.raises(ApplicationError) as exc:
        use_case.execute_external(
            requester_id="user-123",
            requester_name="Fulano",
            type_code="process-issue",
            payload=_payload(),
            branch_code="02",
            idempotency_key=str(uuid4()),
        )
    assert exc.value.code == "requester_invalid"


def test_external_create_requires_valid_branch(harness):
    with pytest.raises(ApplicationError) as exc:
        _external(harness, branch_code="99")
    assert exc.value.code == "branch_invalid"

    with pytest.raises(ApplicationError) as exc:
        _external(harness, branch_code=None)
    assert exc.value.code == "branch_required"


def test_external_create_idempotent_same_key_same_requester(harness):
    requests, idem = harness[1], harness[2]
    key = str(uuid4())
    first = _external(harness, idempotency_key=key)
    second = _external(harness, idempotency_key=key)
    assert second["id"] == first["id"]
    items, total = requests.list_mine(user_id="operator:02:12345")
    assert total == 1 and len(items) == 1

    # mesma chave com OUTRO solicitante externo cria outro request
    other = _external(
        harness, idempotency_key=key, requester_id="operator:02:99999"
    )
    assert other["id"] != first["id"]


# --- validator ----------------------------------------------------------------


def test_validator_accepts_minimal_payload():
    validator = ProcessIssuePayloadValidator()
    payload = _payload(
        issue={"code": "other"},
        operation={
            "productionOrder": "1",
            "operationCode": "03",
            "reportedWorkCenter": "CT-63",
        },
        materialsSnapshotAvailable=False,
        materials=[],
    )
    assert validator.validate(payload) is payload


def test_validator_rejects_unknown_issue_code():
    validator = ProcessIssuePayloadValidator()
    with pytest.raises(ApplicationError) as exc:
        validator.validate(_payload(issue={"code": "unknown_code"}))
    assert exc.value.code == "payload_invalid"


def test_validator_rejects_missing_structure():
    validator = ProcessIssuePayloadValidator()
    for bad in (
        _payload(source="web"),
        _payload(issue=None),
        _payload(operator=None),
        _payload(operation={"productionOrder": "1"}),
        _payload(reportedAt=""),
        _payload(issue={"code": "other", "note": "x" * 501}),
        _payload(materials="nope"),
    ):
        with pytest.raises(ApplicationError):
            validator.validate(bad)


# --- notificações: filial + requester externo ---------------------------------


def test_created_fanout_scopes_processors_by_branch(harness):
    created = _external(harness)
    outbox = harness[3]
    pending = outbox.list_pending()
    assert len(pending) == 1
    payload = pending[0].payload
    assert payload["permissionCodes"] == ["my-requests.process-issue.process"]
    assert payload["requiredPermissionCodes"] == ["my-requests.view.filial-02"]
    assert payload["excludedUserIds"] == ["operator:02:12345"]
    assert created["id"] == pending[0].request_id


def test_external_requester_never_gets_creator_notifications(harness):
    """start/complete de um process-issue não geram dispatch ao operator:*."""
    types, requests, idem, outbox, _ = harness
    created = _external(harness)
    analyst = _user(
        user_id="u-proc",
        permissions=[
            "my-requests.access",
            "my-requests.process-issue.process",
            "my-requests.view.filial-02",
        ],
    )
    use_case = TransitionRequestUseCase(types, requests, idem, outbox=outbox)
    for action in ("start", "complete"):
        use_case.execute(
            user=analyst,
            request_id=created["id"],
            action=action,
            idempotency_key=str(uuid4()),
        )
    creator_dispatches = [
        row
        for row in outbox.list_pending()
        if "operator:" in str(row.payload.get("userIds") or "")
    ]
    assert creator_dispatches == []
    assert is_external_requester_id("operator:02:12345")
    assert not is_external_requester_id("u-proc")


# --- rota S2S -----------------------------------------------------------------


class _SpyUseCase:
    def __init__(self, result=None, exc=None) -> None:
        self.calls: list[dict] = []
        self._result = result or {
            "id": "req-1",
            "request_number": "SOL-000123",
            "type_code": "process-issue",
            "status": "submitted",
            "branch_code": "02",
            "created_at": "2026-10-08T12:00:00+00:00",
        }
        self._exc = exc

    def execute_external(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return dict(self._result)


def _app(use_case, monkeypatch):
    app = FastAPI()
    app.include_router(integrations_routes.router)
    monkeypatch.setattr(
        integrations_routes,
        "build_create_request_use_case",
        lambda: use_case,
    )
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", SERVICE_TOKEN)
    return TestClient(app)


def _s2s_body(**overrides):
    body = {
        "sourceApp": "production-control",
        "typeCode": "process-issue",
        "branch": "02",
        "priority": "normal",
        "requester": {
            "externalId": "operator:02:12345",
            "name": "Maria Silva",
        },
        "payload": _payload(),
    }
    body.update(overrides)
    return body


def _post(api, headers=None, **overrides):
    merged = {**CALLER_HEADERS, "Idempotency-Key": str(uuid4())}
    merged.update(headers or {})
    return api.post("/integrations/requests", json=_s2s_body(**overrides), headers=merged)


def test_s2s_rejects_missing_token(monkeypatch):
    api = _app(_SpyUseCase(), monkeypatch)
    headers = {"X-Delpi-Caller-App": "production-control-api"}
    resp = api.post(
        "/integrations/requests", json=_s2s_body(), headers=headers
    )
    assert resp.status_code == 401


def test_s2s_rejects_wrong_token(monkeypatch):
    api = _app(_SpyUseCase(), monkeypatch)
    resp = _post(api, headers={"X-Delpi-Service-Token": "wrong"})
    assert resp.status_code == 401


def test_s2s_rejects_wrong_caller_app(monkeypatch):
    api = _app(_SpyUseCase(), monkeypatch)
    resp = _post(api, headers={"X-Delpi-Caller-App": "other-api"})
    assert resp.status_code == 403


def test_s2s_rejects_type_outside_allowlist(monkeypatch):
    api = _app(_SpyUseCase(), monkeypatch)
    resp = _post(api, typeCode="invoice-issuance")
    assert resp.status_code == 403


def test_s2s_rejects_source_outside_allowlist(monkeypatch):
    api = _app(_SpyUseCase(), monkeypatch)
    resp = _post(api, sourceApp="other-app")
    assert resp.status_code == 403


def test_s2s_requires_idempotency_key(monkeypatch):
    use_case = _SpyUseCase(
        exc=ApplicationError(code="idempotency_required", status_code=422)
    )
    api = _app(use_case, monkeypatch)
    headers = dict(CALLER_HEADERS)
    resp = api.post("/integrations/requests", json=_s2s_body(), headers=headers)
    assert resp.status_code == 422


def test_s2s_happy_path_returns_request(monkeypatch):
    use_case = _SpyUseCase()
    api = _app(use_case, monkeypatch)
    key = str(uuid4())
    resp = _post(api, headers={"Idempotency-Key": key})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["request_number"] == "SOL-000123"
    assert data["type_code"] == "process-issue"
    assert data["branch_code"] == "02"

    call = use_case.calls[0]
    assert call["requester_id"] == "operator:02:12345"
    assert call["branch_code"] == "02"
    assert call["idempotency_key"] == key
    assert call["payload"]["issue"]["code"] == "tool_not_linked"
