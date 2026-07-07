from __future__ import annotations

from pathlib import Path

import pytest

from tm_app.application.services.processo_arquivo_storage import (
    ProcessoArquivoStorage,
    ProcessoArquivoStorageError,
)


def test_save_and_resolve_file(tmp_path: Path) -> None:
    processo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    storage = ProcessoArquivoStorage(base_dir=str(tmp_path))

    stored_name = storage.save(
        processo_id=processo_id,
        original_name="pop.pdf",
        content=b"pdf-bytes",
        mime_type="application/pdf",
    )

    path = storage.resolve_file(processo_id=processo_id, stored_name=stored_name)
    assert path.read_bytes() == b"pdf-bytes"


def test_validate_upload_rejects_large_file(tmp_path: Path) -> None:
    storage = ProcessoArquivoStorage(base_dir=str(tmp_path))
    with pytest.raises(ProcessoArquivoStorageError, match="25 MB"):
        storage.validate_upload(mime_type="application/pdf", size_bytes=26 * 1024 * 1024)


def test_validate_upload_rejects_invalid_mime(tmp_path: Path) -> None:
    storage = ProcessoArquivoStorage(base_dir=str(tmp_path))
    with pytest.raises(ProcessoArquivoStorageError, match="Formato inválido"):
        storage.validate_upload(mime_type="application/zip", size_bytes=100)
