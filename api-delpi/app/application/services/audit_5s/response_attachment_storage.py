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


class Audit5sResponseAttachmentStorageError(ValueError):
    pass


class Audit5sResponseAttachmentStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.AUDIT_5S_RESPONSE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise Audit5sResponseAttachmentStorageError("Arquivo vazio.")
        if size_bytes > MAX_ATTACHMENT_BYTES:
            raise Audit5sResponseAttachmentStorageError("Arquivo excede o limite de 10 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise Audit5sResponseAttachmentStorageError(
                "Formato inválido. Use JPG, PNG ou WEBP."
            )

    def save(
        self,
        *,
        response_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> tuple[str, str]:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".jpg"

        file_name = f"criterion_{uuid4().hex}{extension}"
        target_dir = self.base_dir / response_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file_name
        target_path.write_bytes(content)
        storage_path = f"{response_id}/{file_name}"
        return file_name, storage_path

    def resolve_file(self, *, response_id: str, file_name: str) -> Path:
        path = (self.base_dir / response_id / file_name).resolve()
        base = self.base_dir.resolve()
        if not str(path).startswith(str(base)):
            raise Audit5sResponseAttachmentStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise Audit5sResponseAttachmentStorageError("Arquivo não encontrado.")
        return path

    def delete_file(self, *, response_id: str, file_name: str) -> None:
        path = (self.base_dir / response_id / file_name).resolve()
        base = self.base_dir.resolve()
        if not str(path).startswith(str(base)):
            raise Audit5sResponseAttachmentStorageError("Caminho de arquivo inválido.")
        if path.is_file():
            path.unlink()

    def delete_response_dir(self, response_id: str) -> None:
        target_dir = (self.base_dir / response_id).resolve()
        base = self.base_dir.resolve()
        if not str(target_dir).startswith(str(base)):
            raise Audit5sResponseAttachmentStorageError("Caminho de diretório inválido.")
        if target_dir.is_dir():
            shutil.rmtree(target_dir)
