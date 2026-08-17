from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

from commercial_app.config import settings

ALLOWED_USER_PHOTO_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_USER_PHOTO_BYTES = 2 * 1024 * 1024
_SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")


class UserProfileStorageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredUserPhoto:
    file_name: str
    storage_key: str
    byte_size: int
    content_type: str


class UserProfileStorage:
    """Binários de foto de usuário — volume COMMERCIAL_USER_AVATAR_UPLOAD_DIR."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.COMMERCIAL_USER_AVATAR_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def identity_dir_name(*, user_id: str) -> str:
        return _SAFE_PART.sub("_", (user_id or "").strip()) or "user"

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise UserProfileStorageError("Arquivo vazio.")
        if size_bytes > MAX_USER_PHOTO_BYTES:
            raise UserProfileStorageError("Arquivo excede o limite de 2 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_USER_PHOTO_MIME_TYPES:
            raise UserProfileStorageError(
                "Formato inválido. Use JPEG, PNG, WebP ou GIF."
            )

    def save(
        self,
        *,
        user_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> StoredUserPhoto:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"
        if extension == ".jpe":
            extension = ".jpg"
        stored_name = f"photo{extension}"
        dir_name = self.identity_dir_name(user_id=user_id)
        target_dir = self.base_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for existing in target_dir.glob("photo.*"):
            existing.unlink(missing_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        storage_key = f"{dir_name}/{stored_name}"
        return StoredUserPhoto(
            file_name=original_name or stored_name,
            storage_key=storage_key,
            byte_size=len(content),
            content_type=(mime_type or "application/octet-stream").lower(),
        )

    def resolve_path(self, storage_key: str) -> Path:
        key = (storage_key or "").strip().lstrip("/")
        if not key or ".." in key.split("/"):
            raise UserProfileStorageError("Chave de armazenamento inválida.")
        path = (self.base_dir / key).resolve()
        if not str(path).startswith(str(self.base_dir.resolve())):
            raise UserProfileStorageError("Chave de armazenamento inválida.")
        return path

    def delete(self, storage_key: str | None) -> None:
        if not storage_key:
            return
        try:
            path = self.resolve_path(storage_key)
        except UserProfileStorageError:
            return
        path.unlink(missing_ok=True)
        parent = path.parent
        if parent != self.base_dir and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
