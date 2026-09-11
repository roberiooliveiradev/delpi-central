"""Completed-by persistence and work-queue mine_scope filters."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
)
from requests_app.domain.entities import Actor, Request
from requests_app.domain.entities.files import RequestArtifact
from requests_app.domain.services.content_loader import load_workflow_definition
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.domain.services.workflow_engine import WorkflowEngine
from requests_app.infrastructure.persistence.repositories.memory_file_repository import (
    InMemoryFileRepository,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


def _creator():
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


def _other_processor():
    return SimpleNamespace(
        id="u-process-2",
        name="Outro",
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
    files = InMemoryFileRepository()
    return types, requests, idem, files


def _issue_with_pdf(types, requests, idem, files, request_id: str) -> None:
    TransitionRequestUseCase(types, requests, idem, files=files).execute(
        user=_processor(),
        request_id=request_id,
        action="start",
        idempotency_key=str(uuid4()),
    )
    files.create_artifact(
        RequestArtifact(
            id=uuid4(),
            request_id=request_id,
            artifact_kind="invoice_pdf",
            original_name="nf.pdf",
            stored_name="nf.pdf",
            storage_key=f"artifacts/{request_id}/nf.pdf",
            mime_type="application/pdf",
            size_bytes=10,
            checksum_sha256="abc",
            produced_by_user_id="u-process",
            produced_by_name="Processador",
        )
    )
    TransitionRequestUseCase(types, requests, idem, files=files).execute(
        user=_processor(),
        request_id=request_id,
        action="issue",
        idempotency_key=str(uuid4()),
    )


def test_confirm_fulfillment_persists_completed_by():
    types, requests, idem, files = _stack()
    created = CreateRequestUseCase(types, requests, idem, files=files).execute(
        user=_creator(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    _issue_with_pdf(types, requests, idem, files, created["id"])
    confirmed = TransitionRequestUseCase(types, requests, idem, files=files).execute(
        user=_creator(),
        request_id=created["id"],
        action="confirm_fulfillment",
        idempotency_key=str(uuid4()),
    )
    assert confirmed["status"] == "completed"
    assert confirmed["completed_by_user_id"] == "u-create"
    assert confirmed["completed_by_name"] == "Criador"
    assert confirmed["completed_at"]


def test_work_queue_completed_by_me_positive_and_negative():
    types, requests, idem, files = _stack()
    # Work queue requires process/manage; confirmer also needs create+ownership.
    creator_processor = SimpleNamespace(
        id="u-create",
        name="Criador",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.invoice-issuance.process",
            "my-requests.view.filial-01",
        ],
    )
    created = CreateRequestUseCase(types, requests, idem, files=files).execute(
        user=creator_processor,
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    _issue_with_pdf(types, requests, idem, files, created["id"])
    TransitionRequestUseCase(types, requests, idem, files=files).execute(
        user=creator_processor,
        request_id=created["id"],
        action="confirm_fulfillment",
        idempotency_key=str(uuid4()),
    )

    mine = ListWorkQueueRequestsUseCase(types, requests).execute(
        user=creator_processor,
        mine_scope="completed_by_me",
    )
    assert mine["total"] == 1
    assert mine["items"][0]["completed_by_user_id"] == "u-create"

    others = ListWorkQueueRequestsUseCase(types, requests).execute(
        user=_processor(),
        mine_scope="completed_by_me",
    )
    assert others["total"] == 0


def test_work_queue_assigned_to_me_sibling():
    types, requests, idem, files = _stack()
    created = CreateRequestUseCase(types, requests, idem, files=files).execute(
        user=_creator(),
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

    mine = ListWorkQueueRequestsUseCase(types, requests).execute(
        user=_processor(),
        mine_scope="assigned_to_me",
    )
    assert mine["total"] == 1

    other = ListWorkQueueRequestsUseCase(types, requests).execute(
        user=_other_processor(),
        mine_scope="assigned_to_me",
    )
    assert other["total"] == 0


def test_engine_sets_completed_by_on_confirm_fulfillment():
    engine = WorkflowEngine()
    workflow = load_workflow_definition("invoice_issuance")
    request = Request(
        id=uuid4(),
        request_number="REQ-1",
        request_type_id=uuid4(),
        type_code="invoice-issuance",
        status="awaiting_requester_confirmation",
        created_by_user_id="u-create",
        created_by_name="Criador",
        version=1,
    )
    result = engine.apply_transition(
        request=request,
        actor=Actor(
            user_id="u-create",
            user_name="Criador",
            has_create=True,
            has_access=True,
        ),
        workflow=workflow,
        action="confirm_fulfillment",
        expected_version=1,
    )
    assert result.request.status == "completed"
    assert result.request.completed_by_user_id == "u-create"
    assert result.request.completed_by_name == "Criador"
    assert result.request.completed_at is not None
