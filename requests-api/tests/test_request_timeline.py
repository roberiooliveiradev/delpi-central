from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.attachment_storage import AttachmentStorage
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


def _timeline(types, requests, files, tmp_path) -> TimelineUseCases:
    return TimelineUseCases(
        types,
        requests,
        files,
        attachment_storage=AttachmentStorage(base_dir=str(tmp_path / "att")),
    )


def test_timeline_comment_and_events(tmp_path):
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
    timeline = _timeline(types, requests, files, tmp_path)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="Preciso de atualização"
    )
    assert comment["body"] == "Preciso de atualização"
    events = timeline.list_events(user=_user(), request_id=created["id"])
    types_seen = {item["event_type"] for item in events["items"]}
    assert "created" in types_seen
    assert "transition" in types_seen
    assert "commented" not in types_seen
    comments = timeline.list_comments(user=_user(), request_id=created["id"])
    assert comments["total"] == 1
    assert comments["items"][0].get("updated_at") is None


def test_comment_edit_marks_updated_at_and_silent_rewrite_does_not(tmp_path):
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
    timeline = _timeline(types, requests, files, tmp_path)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="rascunho"
    )
    silent = timeline.update_comment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        body="rascunho com imagem",
        mark_as_edited=False,
    )
    assert silent.get("updated_at") is None
    edited = timeline.update_comment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        body="texto final",
        mark_as_edited=True,
    )
    assert edited["body"] == "texto final"
    assert edited.get("updated_at") is not None
    listed = timeline.list_comments(user=_user(), request_id=created["id"])
    assert listed["items"][0]["updated_at"] is not None


def test_comment_frozen_when_request_terminal(tmp_path):
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
    stored = requests.get(created["id"])
    assert stored is not None
    stored.status = "completed"
    requests._requests[str(stored.id)] = stored  # noqa: SLF001 — test double

    timeline = _timeline(types, requests, files, tmp_path)
    with pytest.raises(ApplicationError) as exc:
        timeline.create_comment(
            user=_user(), request_id=created["id"], body="depois do fim"
        )
    assert exc.value.code == "conversation_frozen"


def _manager():
    return SimpleNamespace(
        id="u-manager",
        name="Gestor",
        permissions=[
            "my-requests.access",
            "my-requests.manage",
            "my-requests.view.filial-01",
        ],
    )


def test_delete_comment_attachment_author_positive(tmp_path):
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
    timeline = _timeline(types, requests, files, tmp_path)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="com imagem"
    )
    uploaded = timeline.upload_comment_attachment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        original_name="shot.png",
        content=b"\x89PNG\r\n\x1a\n",
        mime_type="image/png",
    )
    listed = timeline.list_comment_attachments(
        user=_user(), request_id=created["id"], comment_id=comment["id"]
    )
    assert len(listed["items"]) == 1

    removed = timeline.delete_comment_attachment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        attachment_id=uploaded["id"],
    )
    assert removed["id"] == uploaded["id"]
    listed_after = timeline.list_comment_attachments(
        user=_user(), request_id=created["id"], comment_id=comment["id"]
    )
    assert listed_after["items"] == []


def test_delete_comment_attachment_manage_sibling(tmp_path):
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
    timeline = _timeline(types, requests, files, tmp_path)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="com imagem"
    )
    uploaded = timeline.upload_comment_attachment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        original_name="shot.png",
        content=b"png-bytes",
        mime_type="image/png",
    )
    timeline.delete_comment_attachment(
        user=_manager(),
        request_id=created["id"],
        comment_id=comment["id"],
        attachment_id=uploaded["id"],
    )
    listed = timeline.list_comment_attachments(
        user=_user(), request_id=created["id"], comment_id=comment["id"]
    )
    assert listed["items"] == []


def test_delete_comment_attachment_forbidden_and_frozen_negative(tmp_path):
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
    timeline = _timeline(types, requests, files, tmp_path)
    comment = timeline.create_comment(
        user=_user(), request_id=created["id"], body="com imagem"
    )
    uploaded = timeline.upload_comment_attachment(
        user=_user(),
        request_id=created["id"],
        comment_id=comment["id"],
        original_name="shot.png",
        content=b"png-bytes",
        mime_type="image/png",
    )

    with pytest.raises(ApplicationError) as forbidden:
        timeline.delete_comment_attachment(
            user=_processor(),
            request_id=created["id"],
            comment_id=comment["id"],
            attachment_id=uploaded["id"],
        )
    assert forbidden.value.code == "delete_forbidden"

    with pytest.raises(ApplicationError) as missing:
        timeline.delete_comment_attachment(
            user=_user(),
            request_id=created["id"],
            comment_id=comment["id"],
            attachment_id=str(uuid4()),
        )
    assert missing.value.code == "attachment_not_found"

    stored = requests.get(created["id"])
    assert stored is not None
    stored.status = "completed"
    requests._requests[str(stored.id)] = stored  # noqa: SLF001 — test double
    with pytest.raises(ApplicationError) as frozen:
        timeline.delete_comment_attachment(
            user=_user(),
            request_id=created["id"],
            comment_id=comment["id"],
            attachment_id=uploaded["id"],
        )
    assert frozen.value.code == "conversation_frozen"
