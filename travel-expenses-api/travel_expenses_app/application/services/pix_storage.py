from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from travel_expenses_app.config import settings

ALLOWED_PIX_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


class PixStorageError(ValueError):
    """Invalid PIX attachment file."""


class PixStorageService:
    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TRAVEL_EXPENSES_PIX_UPLOAD_DIR)
        self.max_bytes = max_bytes or settings.TRAVEL_EXPENSES_RECEIPT_MAX_BYTES

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise PixStorageError("Arquivo vazio.")
        if size_bytes > self.max_bytes:
            raise PixStorageError("Arquivo excede o tamanho máximo permitido.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_PIX_MIME_TYPES:
            raise PixStorageError("Formato inválido. Use JPEG, PNG ou WebP.")

    def save(
        self,
        *,
        report_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(
                (mime_type or "").replace("image/jpg", "image/jpeg")
            ) or ".bin"
        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / report_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name

    def resolve(self, *, report_id: str, stored_name: str) -> Path:
        normalized_name = (stored_name or "").strip()
        if not normalized_name or "/" in normalized_name or "\\" in normalized_name:
            raise PixStorageError("Caminho de arquivo inválido.")
        base = self.base_dir.resolve()
        path = (self.base_dir / report_id / normalized_name).resolve()
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise PixStorageError("Caminho de arquivo inválido.") from exc
        if not path.is_file():
            raise PixStorageError("Arquivo não encontrado.")
        return path

    def delete(self, *, report_id: str, stored_name: str) -> None:
        try:
            path = self.resolve(report_id=report_id, stored_name=stored_name)
        except PixStorageError:
            return
        path.unlink(missing_ok=True)
