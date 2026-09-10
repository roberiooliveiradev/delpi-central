from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    TransitionRequestUseCase,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.gateways.core_notification_adapter import (
    InMemoryPortalNotificationAdapter,
)
from requests_app.infrastructure.persistence.repositories.memory_outbox_repository import (
    InMemoryIntegrationOutboxRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)
from requests_app.infrastructure.schedulers.outbox_worker import PublishOutboxUseCase


def _user():
    return SimpleNamespace(
        id="u-create",
        name="Criador",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.view.filial-01",
        ],
    )


def _processor():
    return SimpleNamespace(
        id="u-process",
        name="Processador",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
    )


def _stack():
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
    outbox = InMemoryIntegrationOutboxRepository()
    return types, requests, idem, outbox


def test_transition_gate_enqueues_creator_outbox_and_worker_publishes():
    types, requests, idem, outbox = _stack()
    created = CreateRequestUseCase(
        types, requests, idem, outbox=outbox
    ).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    assert outbox.list_pending() == []

    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    pending = outbox.list_pending()
    assert len(pending) == 1
    row = pending[0]
    assert row.event_type == "request.transition"
    assert row.payload["category"] == "my_requests"
    assert row.payload["userIds"] == ["u-create"]
    assert row.payload["message"]
    assert row.payload["action"]["type"] == "portal_route"
    assert row.payload["action"]["target"].endswith(created["id"])
    assert row.request_id == created["id"]

    notifier = InMemoryPortalNotificationAdapter()
    published = PublishOutboxUseCase(outbox, notifier).execute()
    assert published == 1
    assert len(notifier.published) == 1
    assert outbox.list_pending() == []


def test_owner_self_transition_does_not_enqueue_outbox():
    types, requests, idem, outbox = _stack()
    created = CreateRequestUseCase(
        types, requests, idem, outbox=outbox
    ).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_processor(),
        request_id=created["id"],
        action="return",
        body={"return_reason": "Falta NF"},
        idempotency_key=str(uuid4()),
    )
    # Clear pending from processor gates so we isolate owner resubmit.
    for row in list(outbox.list_pending()):
        outbox.mark_published(row.id)

    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_user(),
        request_id=created["id"],
        action="resubmit",
        idempotency_key=str(uuid4()),
    )
    assert outbox.list_pending() == []


def test_outbox_dedupe_key_prevents_duplicate_enqueue():
    outbox = InMemoryIntegrationOutboxRepository()
    first = outbox.enqueue(
        event_type="request.created",
        aggregate_type="request",
        aggregate_id="r1",
        payload={"category": "my_requests"},
        dedupe_key="same-key",
    )
    second = outbox.enqueue(
        event_type="request.created",
        aggregate_type="request",
        aggregate_id="r1",
        payload={"category": "my_requests"},
        dedupe_key="same-key",
    )
    assert first.id == second.id
    assert len(outbox.rows) == 1
