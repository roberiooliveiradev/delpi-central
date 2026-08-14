from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.invoice_issuance.attachment_storage import (
    InvoiceIssuanceAttachmentStorage,
    InvoiceIssuanceAttachmentStorageError,
)


def test_saves_pdf_under_request_dir(tmp_path: Path) -> None:
    storage = InvoiceIssuanceAttachmentStorage(base_dir=str(tmp_path))
    stored = storage.save(
        request_id="req-1",
        original_name="pedido.pdf",
        content=b"%PDF-1.4 test",
        mime_type="application/pdf",
    )
    assert stored.endswith(".pdf")
    assert (tmp_path / "req-1" / stored).is_file()


def test_rejects_non_pdf(tmp_path: Path) -> None:
    storage = InvoiceIssuanceAttachmentStorage(base_dir=str(tmp_path))
    with pytest.raises(InvoiceIssuanceAttachmentStorageError):
        storage.save(
            request_id="req-1",
            original_name="foto.png",
            content=b"not-a-pdf",
            mime_type="image/png",
        )
