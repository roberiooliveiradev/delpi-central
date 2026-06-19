from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.application.services.chat_drawing_library_attachment_service import (
    ChatDrawingLibraryAttachmentService,
)


@pytest.fixture()
def library_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CHAT_ATTACHMENT_STORAGE_PATH", str(tmp_path))


def _session(user_id: UUID | None = None):
    return SimpleNamespace(
        user_id=user_id or uuid4(),
        project_id=None,
        agent_id=None,
    )


def test_merge_into_turn_attachments_registers_library_pdf(library_env, tmp_path: Path) -> None:
    user_id = uuid4()
    session_id = uuid4()
    session = _session(user_id)
    cache_pdf = tmp_path / "90262957.pdf"
    cache_pdf.write_bytes(b"%PDF-1.4 cached")

    created = SimpleNamespace(
        id=uuid4(),
        filename="stored.pdf",
        original_filename="90262957.pdf",
        content_type="application/pdf",
        size_bytes=len(cache_pdf.read_bytes()),
        status="uploaded",
        storage_path=str(tmp_path / "stored.pdf"),
        metadata={},
    )
    indexed = SimpleNamespace(
        id=created.id,
        filename=created.filename,
        original_filename=created.original_filename,
        content_type=created.content_type,
        size_bytes=created.size_bytes,
        status="indexed",
        storage_path=created.storage_path,
        metadata={
            "source": "api_delpi_library",
            "productCode": "90262957",
            "indexed": True,
            "preview": {"kind": "document"},
        },
    )

    class FakeAttachmentRepository:
        def list_session_attachments(self, *, user_id, session_id):
            return []

        def create_attachment(self, **kwargs):
            created.storage_path = kwargs["storage_path"]
            Path(kwargs["storage_path"]).write_bytes(cache_pdf.read_bytes())
            created.metadata = kwargs["metadata"]
            return created

        def update_status(self, *, attachment_id, status, metadata=None):
            assert attachment_id == created.id
            assert status == "indexed"
            return indexed

    tool_context = {
        "drawingAnalysisMode": True,
        "drawingLibraryFetch": {
            "productCode": "90262957",
            "filename": "90262957.pdf",
            "storagePath": str(cache_pdf),
            "source": "api_delpi_library",
        },
        "drawingPdfExtractSummary": {
            "legible": True,
            "charCount": 1200,
            "documentVision": {"legible": True, "engine": "tesseract"},
        },
    }

    result = ChatDrawingLibraryAttachmentService.merge_into_turn_attachments(
        [],
        user_id=user_id,
        session_id=session_id,
        tool_context=tool_context,
        attachment_repository=FakeAttachmentRepository(),
        session=session,
    )

    assert len(result) == 1
    assert result[0]["original_filename"] == "90262957.pdf"
    assert result[0]["status"] == "indexed"
    assert result[0]["id"] == str(created.id)


def test_merge_into_turn_attachments_keeps_user_attachments() -> None:
    existing = [{"id": "att-1", "original_filename": "manual.pdf"}]

    result = ChatDrawingLibraryAttachmentService.merge_into_turn_attachments(
        existing,
        user_id=uuid4(),
        session_id=uuid4(),
        tool_context={"drawingAnalysisMode": True, "drawingLibraryFetch": {}},
        attachment_repository=object(),
        session=_session(),
    )

    assert result == existing


def test_merge_into_turn_attachments_skips_without_library_fetch() -> None:
    result = ChatDrawingLibraryAttachmentService.merge_into_turn_attachments(
        [],
        user_id=uuid4(),
        session_id=uuid4(),
        tool_context={"drawingAnalysisMode": True},
        attachment_repository=object(),
        session=_session(),
    )

    assert result == []
