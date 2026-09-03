from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.attachment_storage import (
    AttachmentStorage,
    ArtifactStorage,
    StorageError,
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
from requests_app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    list_migration_files,
)


def test_v004_in_migration_list():
    names = [path.name for path in list_migration_files()]
    assert "V004__attachments_artifacts_events.sql" in names
    sql = (MIGRATIONS_DIR / "V004__attachments_artifacts_events.sql").read_text(
        encoding="utf-8"
    )
    assert "request_attachments" in sql
    assert "request_artifacts" in sql
    assert "request_events" in sql


def test_attachment_storage_roundtrip(tmp_path: Path):
    storage = AttachmentStorage(base_dir=str(tmp_path / "att"))
    stored = storage.save(
        request_id=str(uuid4()),
        original_name="nota.pdf",
        content=b"%PDF-1.4 test",
        mime_type="application/pdf",
    )
    path = storage.resolve_file(storage_key=stored.storage_key)
    assert path.read_bytes() == b"%PDF-1.4 test"
    assert stored.checksum_sha256


def test_attachment_rejects_bad_mime(tmp_path: Path):
    storage = AttachmentStorage(base_dir=str(tmp_path / "att"))
    with pytest.raises(StorageError):
        storage.save(
            request_id="r1",
            original_name="x.exe",
            content=b"abc",
            mime_type="application/x-msdownload",
        )


def test_path_traversal_blocked(tmp_path: Path):
    storage = AttachmentStorage(base_dir=str(tmp_path / "att"))
    with pytest.raises(StorageError):
        storage.resolve_file(storage_key="../etc/passwd")


def _user(permissions=None):
    return SimpleNamespace(
        id="u-create",
        name="Criador",
        permissions=permissions
        or [
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
def file_harness(tmp_path: Path):
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
    return use_cases, created, files


def test_upload_attachment_and_event(file_harness):
    use_cases, created, files = file_harness
    result = use_cases.upload_attachment(
        user=_user(),
        request_id=created["id"],
        original_name="doc.pdf",
        content=b"%PDF-ok",
        mime_type="application/pdf",
    )
    assert result["original_name"] == "doc.pdf"
    listed = use_cases.list_attachments(user=_user(), request_id=created["id"])
    assert listed["items"]
    events, total = files.list_events(created["id"])
    assert total >= 1
    assert any(e.event_type == "attachment_added" for e in events)


def test_artifact_upload_requires_process(file_harness):
    use_cases, created, _ = file_harness
    with pytest.raises(ApplicationError) as exc:
        use_cases.upload_artifact(
            user=_user(),
            request_id=created["id"],
            original_name="nf.pdf",
            content=b"%PDF-nf",
            mime_type="application/pdf",
        )
    assert exc.value.code == "upload_forbidden"
    ok = use_cases.upload_artifact(
        user=_processor(),
        request_id=created["id"],
        original_name="nf.pdf",
        content=b"%PDF-nf",
        mime_type="application/pdf",
        artifact_kind="invoice_pdf",
    )
    assert ok["artifact_kind"] == "invoice_pdf"
