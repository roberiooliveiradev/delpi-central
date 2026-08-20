from __future__ import annotations

import mimetypes
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from commercial_app.config import settings
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

ALLOWED_ATTACHMENT_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
# Fallback se o JSON de settings não carregar (alinhado a messageAttachmentMaxBytes).
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")


class AttachmentStorageError(ValueError):
    pass


def attachment_max_bytes() -> int:
    return max(
        1,
        InteractionRoomContentService.setting_int(
            "messageAttachmentMaxBytes",
            MAX_ATTACHMENT_BYTES,
        ),
    )


def attachment_max_count() -> int:
    return max(
        1,
        InteractionRoomContentService.setting_int("messageAttachmentMaxCount", 10),
    )


@dataclass(frozen=True, slots=True)
class StoredAttachment:
    file_name: str
    storage_key: str
    byte_size: int


class AttachmentStorage:
    """Binários de anexos — volume COMMERCIAL_ATTACHMENT_UPLOAD_DIR."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.COMMERCIAL_ATTACHMENT_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise AttachmentStorageError("Arquivo vazio.")
        limit = attachment_max_bytes()
        if size_bytes > limit:
            max_mb = max(1, limit // (1024 * 1024))
            raise AttachmentStorageError(
                InteractionRoomContentService.error(
                    "attachmentTooLarge",
                    maxMb=str(max_mb),
                )
            )
        normalized = (mime_type or "").lower().split(";")[0].strip()
        if normalized not in ALLOWED_ATTACHMENT_MIME_TYPES:
            raise AttachmentStorageError(
                "Formato inválido. Use PDF, imagem, TXT, Word ou Excel."
            )

    @staticmethod
    def _safe_owner_dir(*, owner_type: str, owner_id: str) -> str:
        kind = _SAFE_PART.sub("_", (owner_type or "").strip()) or "owner"
        oid = _SAFE_PART.sub("_", (owner_id or "").strip()) or "id"
        return f"{kind}/{oid}"

    def save(
        self,
        *,
        owner_type: str,
        owner_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> StoredAttachment:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension((mime_type or "").split(";")[0].strip()) or ".bin"
        if extension == ".jpe":
            extension = ".jpg"
        display_name = Path(original_name).name.strip() or f"anexo{extension}"
        display_name = _SAFE_PART.sub("_", display_name) or f"anexo{extension}"
        stored_name = f"{uuid.uuid4().hex}{extension}"
        dir_name = self._safe_owner_dir(owner_type=owner_type, owner_id=owner_id)
        target_dir = self.base_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        storage_key = f"{dir_name}/{stored_name}"
        return StoredAttachment(
            file_name=display_name,
            storage_key=storage_key,
            byte_size=len(content),
        )

    def resolve_file(self, *, storage_key: str) -> Path:
        base = self.base_dir.resolve()
        normalized_key = storage_key.strip().lstrip("/")
        if not normalized_key or ".." in normalized_key.split("/"):
            raise AttachmentStorageError("Caminho de arquivo inválido.")
        path = (self.base_dir / normalized_key).resolve()
        if not str(path).startswith(str(base)):
            raise AttachmentStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise AttachmentStorageError("Arquivo não encontrado.")
        return path

    def delete(self, *, storage_key: str) -> None:
        try:
            path = self.resolve_file(storage_key=storage_key)
        except AttachmentStorageError:
            return
        path.unlink(missing_ok=True)
        parent = path.parent
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass
