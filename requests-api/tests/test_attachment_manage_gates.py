from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.attachment_storage import (
    ArtifactStorage,
    AttachmentStorage,
)
from requests_app.application.use_cases.file_use_cases import FileUseCases
from requests_app.application.use_cases.request_use_cases import CreateRequestUseCase
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


@pytest.fixture
def manage_harness(tmp_path: Path):
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
    created = CreateRequestUseCase(types, requests, idem).execute(
        user=_user(),
        type_code="invoice-issuance",
        payload={},
        branch_code="01",
        idempotency_key=str(uuid4()),
    )
    use_cases = FileUseCases(
        types,
        requests,
        files,
        AttachmentStorage(base_dir=str(tmp_path / "att")),
        ArtifactStorage(base_dir=str(tmp_path / "art")),
    )
    return use_cases, created, files, requests


def test_owner_upload_ok_on_submitted_bootstrap(manage_harness):
    use_cases, created, *_ = manage_harness
    result = use_cases.upload_attachment(
        user=_user(),
        request_id=created["id"],
        original_name="doc.pdf",
        content=b"%PDF-ok",
        mime_type="application/pdf",
    )
    assert result["original_name"] == "doc.pdf"


def test_staff_cannot_upload_attachment(manage_harness):
    use_cases, created, *_ = manage_harness
    with pytest.raises(ApplicationError) as exc:
        use_cases.upload_attachment(
            user=_processor(),
            request_id=created["id"],
            original_name="doc.pdf",
            content=b"%PDF-ok",
            mime_type="application/pdf",
        )
    assert exc.value.code == "upload_forbidden"


def test_owner_upload_forbidden_in_progress(manage_harness):
    use_cases, created, _, requests = manage_harness
    entity = requests.get(created["id"])
    assert entity is not None
    entity.status = "in_progress"
    requests.update(entity, expected_version=entity.version)
    with pytest.raises(ApplicationError) as exc:
        use_cases.upload_attachment(
            user=_user(),
            request_id=created["id"],
            original_name="doc.pdf",
            content=b"%PDF-ok",
            mime_type="application/pdf",
        )
    assert exc.value.code == "upload_forbidden"


def test_owner_delete_only_when_needs_information(manage_harness):
    use_cases, created, files, requests = manage_harness
    uploaded = use_cases.upload_attachment(
        user=_user(),
        request_id=created["id"],
        original_name="doc.pdf",
        content=b"%PDF-ok",
        mime_type="application/pdf",
    )
    with pytest.raises(ApplicationError) as exc:
        use_cases.delete_attachment(user=_user(), attachment_id=str(uploaded["id"]))
    assert exc.value.code == "delete_forbidden"

    entity = requests.get(created["id"])
    assert entity is not None
    entity.status = "needs_information"
    requests.update(entity, expected_version=entity.version)

    deleted = use_cases.delete_attachment(
        user=_user(),
        attachment_id=str(uploaded["id"]),
    )
    assert deleted["deleted"] is True
    assert files.get_attachment(uploaded["id"]) is None
    events, _ = files.list_events(created["id"])
    assert any(e.event_type == "attachment_removed" for e in events)
