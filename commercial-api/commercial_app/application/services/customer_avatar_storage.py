from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

from commercial_app.config import settings

ALLOWED_AVATAR_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_AVATAR_BYTES = 2 * 1024 * 1024
_SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")


class CustomerAvatarStorageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredAvatar:
    file_name: str
    storage_key: str
    byte_size: int


class CustomerAvatarStorage:
    """Binários de logo do cliente — volume COMMERCIAL_AVATAR_UPLOAD_DIR."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.COMMERCIAL_AVATAR_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def identity_dir_name(*, customer_code: str, customer_store: str) -> str:
        code = _SAFE_PART.sub("_", (customer_code or "").strip()) or "code"
        store = _SAFE_PART.sub("_", (customer_store or "").strip()) or "store"
        return f"{code}__{store}"

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise CustomerAvatarStorageError("Arquivo vazio.")
        if size_bytes > MAX_AVATAR_BYTES:
            raise CustomerAvatarStorageError("Arquivo excede o limite de 2 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_AVATAR_MIME_TYPES:
            raise CustomerAvatarStorageError(
                "Formato inválido. Use JPEG, PNG, WebP ou GIF."
            )

    def save(
        self,
        *,
        customer_code: str,
        customer_store: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> StoredAvatar:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"
        if extension == ".jpe":
            extension = ".jpg"
        stored_name = f"avatar{extension}"
        dir_name = self.identity_dir_name(
            customer_code=customer_code,
            customer_store=customer_store,
        )
        target_dir = self.base_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for existing in target_dir.glob("avatar.*"):
            existing.unlink(missing_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        storage_key = f"{dir_name}/{stored_name}"
        return StoredAvatar(
            file_name=stored_name,
            storage_key=storage_key,
            byte_size=len(content),
        )

    def resolve_file(
        self,
        *,
        customer_code: str,
        customer_store: str,
        storage_key: str | None = None,
        file_name: str | None = None,
    ) -> Path:
        base = self.base_dir.resolve()
        if storage_key:
            normalized_key = storage_key.strip().lstrip("/")
            if ".." in normalized_key.split("/"):
                raise CustomerAvatarStorageError("Caminho de arquivo inválido.")
            path = (self.base_dir / normalized_key).resolve()
        else:
            normalized_name = (file_name or "").strip()
            if not normalized_name or "/" in normalized_name or "\\" in normalized_name:
                raise CustomerAvatarStorageError("Arquivo não encontrado.")
            path = (
                self.base_dir
                / self.identity_dir_name(
                    customer_code=customer_code,
                    customer_store=customer_store,
                )
                / normalized_name
            ).resolve()
        if not str(path).startswith(str(base)):
            raise CustomerAvatarStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise CustomerAvatarStorageError("Arquivo não encontrado.")
        return path

    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
        storage_key: str | None = None,
        file_name: str | None = None,
    ) -> None:
        target_dir = self.base_dir / self.identity_dir_name(
            customer_code=customer_code,
            customer_store=customer_store,
        )
        if storage_key:
            path = self.base_dir / storage_key.lstrip("/")
            if path.is_file():
                path.unlink(missing_ok=True)
        elif file_name:
            path = target_dir / file_name
            if path.is_file():
                path.unlink(missing_ok=True)
        if target_dir.is_dir():
            for existing in target_dir.glob("avatar.*"):
                existing.unlink(missing_ok=True)
            try:
                target_dir.rmdir()
            except OSError:
                pass
