from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    TransitionRequestUseCase,
)
from requests_app.application.use_cases.timeline_use_cases import TimelineUseCases
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.persistence.repositories.memory_file_repository import (
    InMemoryFileRepository,
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


def test_timeline_comment_and_events():
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
    files = InMemoryFileRepository()
    created = CreateRequestUseCase(types, requests, idem, files=files).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    TransitionRequestUseCase(types, requests, idem, files=files).execute(
        user=_processor(),
        request_id=created["id"],
        action="start",
        idempotency_key=str(uuid4()),
    )
    timeline = TimelineUseCases(types, requests, files)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="Preciso de atualização"
    )
    assert comment["body"] == "Preciso de atualização"
    events = timeline.list_events(user=_user(), request_id=created["id"])
    types_seen = {item["event_type"] for item in events["items"]}
    assert "created" in types_seen
    assert "transition" in types_seen
    assert "commented" in types_seen
    comments = timeline.list_comments(user=_user(), request_id=created["id"])
    assert comments["total"] == 1
