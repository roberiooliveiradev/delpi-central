from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from app.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


class Audit5sNcAttachmentStorageError(ValueError):
    pass


class Audit5sNcAttachmentStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.AUDIT_5S_NC_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise Audit5sNcAttachmentStorageError("Arquivo vazio.")
        if size_bytes > MAX_ATTACHMENT_BYTES:
            raise Audit5sNcAttachmentStorageError("Arquivo excede o limite de 10 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise Audit5sNcAttachmentStorageError(
                "Formato inválido. Use JPG, PNG ou WEBP."
            )

    def save(
        self,
        *,
        nonconformity_id: str,
        attachment_type: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".jpg"

        stored_name = f"{attachment_type}_{uuid4().hex}{extension}"
        target_dir = self.base_dir / nonconformity_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name

    def resolve_file(self, *, nonconformity_id: str, stored_name: str) -> Path:
        path = (self.base_dir / nonconformity_id / stored_name).resolve()
        base = self.base_dir.resolve()
        if not str(path).startswith(str(base)):
            raise Audit5sNcAttachmentStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise Audit5sNcAttachmentStorageError("Arquivo não encontrado.")
        return path

    def delete_nonconformity_dir(self, nonconformity_id: str) -> None:
        target_dir = (self.base_dir / nonconformity_id).resolve()
        base = self.base_dir.resolve()
        if not str(target_dir).startswith(str(base)):
            raise Audit5sNcAttachmentStorageError("Caminho de diretório inválido.")
        if target_dir.is_dir():
            shutil.rmtree(target_dir)
