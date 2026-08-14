from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from app.config import settings

ALLOWED_MIME_TYPES = {"application/pdf"}
MAX_BYTES = 25 * 1024 * 1024


class InvoiceIssuanceAttachmentStorageError(ValueError):
    pass


class InvoiceIssuanceAttachmentStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.INVOICE_ISSUANCE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise InvoiceIssuanceAttachmentStorageError("Arquivo vazio.")
        if size_bytes > MAX_BYTES:
            raise InvoiceIssuanceAttachmentStorageError("Arquivo excede o limite de 25 MB.")
        normalized = (mime_type or "").lower()
        name_ok = normalized in ALLOWED_MIME_TYPES or normalized == "application/octet-stream"
        if not name_ok:
            raise InvoiceIssuanceAttachmentStorageError("Anexe um PDF do pedido de compra.")

    def save(
        self,
        *,
        request_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        guessed = mime_type or mimetypes.guess_type(original_name)[0]
        if (original_name or "").lower().endswith(".pdf"):
            guessed = guessed or "application/pdf"
        self.validate_upload(mime_type=guessed, size_bytes=len(content))
        stored_name = f"{uuid4().hex}.pdf"
        target_dir = self.base_dir / request_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / stored_name).write_bytes(content)
        return stored_name
