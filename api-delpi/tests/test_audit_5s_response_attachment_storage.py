from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.audit_5s.response_attachment_storage import (
    Audit5sResponseAttachmentStorage,
    Audit5sResponseAttachmentStorageError,
)


def test_save_and_resolve_response_attachment(tmp_path: Path) -> None:
    storage = Audit5sResponseAttachmentStorage(base_dir=str(tmp_path))
    file_name, storage_path = storage.save(
        response_id="resp-1",
        original_name="antes.jpg",
        content=b"fake-image",
        mime_type="image/jpeg",
    )

    assert storage_path == f"resp-1/{file_name}"
    path = storage.resolve_file(response_id="resp-1", file_name=file_name)
    assert path.read_bytes() == b"fake-image"


def test_reject_invalid_mime(tmp_path: Path) -> None:
    storage = Audit5sResponseAttachmentStorage(base_dir=str(tmp_path))
    with pytest.raises(Audit5sResponseAttachmentStorageError, match="Formato inválido"):
        storage.save(
            response_id="resp-1",
            original_name="doc.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )


def test_reject_empty_file(tmp_path: Path) -> None:
    storage = Audit5sResponseAttachmentStorage(base_dir=str(tmp_path))
    with pytest.raises(Audit5sResponseAttachmentStorageError, match="Arquivo vazio"):
        storage.validate_upload(mime_type="image/jpeg", size_bytes=0)


def test_delete_response_dir(tmp_path: Path) -> None:
    storage = Audit5sResponseAttachmentStorage(base_dir=str(tmp_path))
    file_name, _ = storage.save(
        response_id="resp-2",
        original_name="foto.png",
        content=b"png-bytes",
        mime_type="image/png",
    )
    assert storage.resolve_file(response_id="resp-2", file_name=file_name).is_file()
    storage.delete_response_dir("resp-2")
    with pytest.raises(Audit5sResponseAttachmentStorageError):
        storage.resolve_file(response_id="resp-2", file_name=file_name)
