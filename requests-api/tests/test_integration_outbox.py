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


def test_create_and_transition_enqueue_outbox_and_worker_publishes():
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
    pending = outbox.list_pending()
    assert len(pending) == 2
    assert {row.event_type for row in pending} == {
        "request.created",
        "request.transition",
    }
    for row in pending:
        assert row.payload["category"] == "my_requests"
        assert row.request_id == created["id"]

    notifier = InMemoryPortalNotificationAdapter()
    published = PublishOutboxUseCase(outbox, notifier).execute()
    assert published == 2
    assert len(notifier.published) == 2
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
