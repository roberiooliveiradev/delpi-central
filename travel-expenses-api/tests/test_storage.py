from pathlib import Path

import pytest

from travel_expenses_app.application.services.receipt_storage import (
    ReceiptStorageError,
    ReceiptStorageService,
)


def test_save_and_resolve_and_reject_traversal(tmp_path: Path):
    storage = ReceiptStorageService(base_dir=str(tmp_path), max_bytes=1024)
    stored = storage.save(
        report_id="rep-1",
        original_name="cupom.jpg",
        content=b"jpeg-bytes",
        mime_type="image/jpeg",
    )
    path = storage.resolve(report_id="rep-1", stored_name=stored)
    assert path.read_bytes() == b"jpeg-bytes"

    with pytest.raises(ReceiptStorageError):
        storage.resolve(report_id="rep-1", stored_name="../secret.bin")


def test_rejects_invalid_mime(tmp_path: Path):
    storage = ReceiptStorageService(base_dir=str(tmp_path), max_bytes=1024)
    with pytest.raises(ReceiptStorageError):
        storage.save(
            report_id="rep-1",
            original_name="virus.exe",
            content=b"x",
            mime_type="application/x-msdownload",
        )
