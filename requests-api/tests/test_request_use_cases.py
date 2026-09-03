from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    GetRequestUseCase,
    ListMyRequestsUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
    UpdateRequestPayloadUseCase,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


def _user(*, user_id: str = "u-create", permissions: list[str] | None = None):
    return SimpleNamespace(
        id=user_id,
        name="Usuário Teste",
        permissions=permissions
        or [
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.view.filial-01",
        ],
    )


def _processor_user():
    return _user(
        user_id="u-process",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
    )


@pytest.fixture
def harness():
    invoice = RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    )
    types = InMemoryRequestTypeRepository([invoice])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    return types, requests, idem


def test_create_start_allowed_actions(harness):
    types, requests, idem = harness
    created = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"items": [{"product_code": "X"}]},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    assert created["status"] == "submitted"
    assert created["status_alias"] == "pending"
    assert "cancel" in created["allowed_actions"]

    started = TransitionRequestUseCase(types, requests, idem).execute(
        user=_processor_user(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    assert started["status"] == "in_progress"
    actions = set(started["allowed_actions"])
    assert {"view", "return", "complete", "issue", "cancel"} <= actions


def test_idempotency_replay_does_not_duplicate(harness):
    types, requests, idem = harness
    key = str(uuid4())
    first = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"ok": True},
        branch_code="01",
        idempotency_key=key,
    )
    second = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"ok": True},
        branch_code="01",
        idempotency_key=key,
    )
    assert first["id"] == second["id"]
    assert first["request_number"] == second["request_number"]
    mine = ListMyRequestsUseCase(types, requests).execute(user=_user())
    assert mine["total"] == 1


def test_branch_forbidden_without_filial_permission(harness):
    types, requests, idem = harness
    user = _user(
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            # sem filial-01
        ]
    )
    with pytest.raises(ApplicationError) as exc:
        CreateRequestUseCase(types, requests, idem).execute(
            user=user,
            type_code="invoice-issuance",
            payload={},
            branch_code="01",
            idempotency_key=str(uuid4()),
        )
    assert exc.value.code == "branch_forbidden"
    assert exc.value.status_code == 403


def test_stale_version_on_transition(harness):
    types, requests, idem = harness
    created = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    with pytest.raises(ApplicationError) as exc:
        TransitionRequestUseCase(types, requests, idem).execute(
            user=_processor_user(),
            request_id=created["id"],
            action="start",
            expected_version=99,
            idempotency_key=str(uuid4()),
        )
    assert exc.value.code == "stale_version"
    assert exc.value.status_code == 409


def test_edit_and_resubmit_flow(harness):
    types, requests, idem = harness
    created = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={"a": 1},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    TransitionRequestUseCase(types, requests, idem).execute(
        user=_processor_user(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    TransitionRequestUseCase(types, requests, idem).execute(
        user=_processor_user(),
        request_id=created["id"],
        action="return",
        body={"return_reason": "Corrigir item"},
        idempotency_key=str(uuid4()),
    )
    edited = UpdateRequestPayloadUseCase(types, requests, idem).execute(
        user=_user(),
        request_id=created["id"],
        payload={"a": 2},
        idempotency_key=str(uuid4()),
    )
    assert edited["payload"]["a"] == 2
    assert "edit" in edited["allowed_actions"]
    resubmitted = TransitionRequestUseCase(types, requests, idem).execute(
        user=_user(),
        request_id=created["id"],
        action="resubmit",
        idempotency_key=str(uuid4()),
    )
    assert resubmitted["status"] == "submitted"


def test_work_queue_lists_for_processor(harness):
    types, requests, idem = harness
    CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    queue = ListWorkQueueRequestsUseCase(types, requests).execute(user=_processor_user())
    assert queue["total"] == 1
    detail = GetRequestUseCase(types, requests).execute(
        user=_processor_user(), request_id=queue["items"][0]["id"]
    )
    assert "start" in detail["allowed_actions"]
