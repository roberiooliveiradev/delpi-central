"""Attendant (assignee / queue) Portal notification policy and fan-out."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from requests_app.application.services.attachment_storage import AttachmentStorage
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    TransitionRequestUseCase,
)
from requests_app.application.use_cases.timeline_use_cases import TimelineUseCases
from requests_app.domain.services.attendant_portal_notification_policy import (
    should_notify_assignee,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_file_repository import (
    InMemoryFileRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_outbox_repository import (
    InMemoryIntegrationOutboxRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


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
    files = InMemoryFileRepository()
    return types, requests, idem, outbox, files


def test_should_notify_assignee_positive_and_negative():
    assert should_notify_assignee(
        actor_user_id="u-create", assignee_user_id="u-process"
    )
    assert not should_notify_assignee(
        actor_user_id="u-process", assignee_user_id="u-process"
    )
    assert not should_notify_assignee(actor_user_id="u-create", assignee_user_id=None)


def test_create_enqueues_processor_permission_fanout():
    types, requests, idem, outbox, _files = _stack()
    created = CreateRequestUseCase(
        types, requests, idem, outbox=outbox
    ).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    pending = outbox.list_pending()
    assert len(pending) == 1
    row = pending[0]
    assert row.event_type == "request.created"
    assert row.payload["permissionCodes"] == [
        "my-requests.invoice-issuance.process"
    ]
    assert row.payload["excludedUserIds"] == ["u-create"]
    assert "userIds" not in row.payload
    assert created["id"] == row.request_id


def test_comment_from_owner_notifies_assignee_not_self(tmp_path):
    types, requests, idem, outbox, files = _stack()
    created = CreateRequestUseCase(
        types, requests, idem, outbox=outbox
    ).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    for row in list(outbox.list_pending()):
        outbox.mark_published(row.id)

    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    for row in list(outbox.list_pending()):
        outbox.mark_published(row.id)

    storage = AttachmentStorage(base_dir=tmp_path / "attachments")
    TimelineUseCases(
        types, requests, files, attachment_storage=storage, outbox=outbox
    ).create_comment(
        user=_user(),
        request_id=created["id"],
        body="Preciso atualizar o destinatário",
    )
    pending = outbox.list_pending()
    assert len(pending) == 1
    row = pending[0]
    assert row.event_type == "request.comment"
    assert row.payload["userIds"] == ["u-process"]
    assert "Novo comentário" in row.payload["title"]


def test_comment_from_assignee_notifies_creator_only(tmp_path):
    types, requests, idem, outbox, files = _stack()
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
    for row in list(outbox.list_pending()):
        outbox.mark_published(row.id)

    storage = AttachmentStorage(base_dir=tmp_path / "attachments")
    TimelineUseCases(
        types, requests, files, attachment_storage=storage, outbox=outbox
    ).create_comment(
        user=_processor(),
        request_id=created["id"],
        body="Vou emitir hoje",
    )
    pending = outbox.list_pending()
    assert len(pending) == 1
    assert pending[0].payload["userIds"] == ["u-create"]


def test_owner_resubmit_notifies_assignee():
    types, requests, idem, outbox, _files = _stack()
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
    for row in list(outbox.list_pending()):
        outbox.mark_published(row.id)

    TransitionRequestUseCase(types, requests, idem, outbox=outbox).execute(
        user=_user(),
        request_id=created["id"],
        action="resubmit",
        idempotency_key=str(uuid4()),
    )
    pending = outbox.list_pending()
    assert len(pending) == 1
    assert pending[0].payload["userIds"] == ["u-process"]
    assert "reenviada" in pending[0].payload["message"].lower()
