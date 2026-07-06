from __future__ import annotations

from pathlib import Path

import pytest

from tm_app.application.services.revisao_evidence_storage import (
    RevisaoEvidenceStorage,
    RevisaoEvidenceStorageError,
)


def test_save_and_resolve_file(tmp_path: Path) -> None:
    revisao_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    storage = RevisaoEvidenceStorage(base_dir=str(tmp_path))

    stored_name = storage.save(
        revisao_id=revisao_id,
        original_name="foto.png",
        content=b"png-bytes",
        mime_type="image/png",
    )

    path = storage.resolve_file(revisao_id=revisao_id, stored_name=stored_name)
    assert path.read_bytes() == b"png-bytes"


def test_validate_upload_rejects_large_file(tmp_path: Path) -> None:
    storage = RevisaoEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(RevisaoEvidenceStorageError, match="25 MB"):
        storage.validate_upload(mime_type="image/png", size_bytes=26 * 1024 * 1024)


def test_validate_upload_rejects_invalid_mime(tmp_path: Path) -> None:
    storage = RevisaoEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(RevisaoEvidenceStorageError, match="Formato inválido"):
        storage.validate_upload(mime_type="application/zip", size_bytes=100)


def test_resolve_file_missing_raises(tmp_path: Path) -> None:
    storage = RevisaoEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(RevisaoEvidenceStorageError, match="Arquivo não encontrado"):
        storage.resolve_file(revisao_id="rev-1", stored_name="missing.pdf")
