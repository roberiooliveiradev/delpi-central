from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetDocumentTooLargeError,
    BudgetDocumentTypeNotAllowedError,
)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-powerpoint",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "video/mp4",
    "video/webm",
}

EXT_TO_KIND = {
    ".pdf": "pdf",
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".csv": "spreadsheet",
    ".pptx": "presentation",
    ".ppt": "presentation",
    ".doc": "document",
    ".docx": "document",
    ".txt": "document",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".gif": "image",
    ".mp4": "video",
    ".webm": "video",
}

MAX_DOCUMENT_BYTES = 25 * 1024 * 1024


class BudgetDocumentStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def check_size(self, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise BudgetDocumentTypeNotAllowedError("Arquivo vazio.")
        if size_bytes > MAX_DOCUMENT_BYTES:
            raise BudgetDocumentTooLargeError("Arquivo excede o limite de 25 MB.")

    def check_mime(self, mime_type: str | None) -> str:
        normalized = (mime_type or "").lower().strip()
        if normalized not in ALLOWED_MIME_TYPES:
            raise BudgetDocumentTypeNotAllowedError("Tipo de arquivo não permitido.")
        return normalized

    def check_extension(self, original_name: str) -> str:
        extension = Path(original_name or "").suffix.lower()
        kind = EXT_TO_KIND.get(extension)
        if kind is None:
            raise BudgetDocumentTypeNotAllowedError("Extensão de arquivo não permitida.")
        return kind

    def validate_upload(self, *, mime_type: str | None, size_bytes: int, original_name: str) -> str:
        self.check_size(size_bytes)
        self.check_mime(mime_type)
        return self.check_extension(original_name)

    def save(
        self,
        *,
        exercise_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> tuple[str, str]:
        kind = self.validate_upload(
            mime_type=mime_type,
            size_bytes=len(content),
            original_name=original_name,
        )
        extension = Path(original_name).suffix.lower() or (
            mimetypes.guess_extension(mime_type or "") or ".bin"
        )
        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / exercise_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name, kind

    def resolve_file(self, *, exercise_id: str, storage_key: str) -> Path:
        key = (storage_key or "").strip()
        if not key or "/" in key or "\\" in key or key.startswith("."):
            raise BudgetDocumentTypeNotAllowedError("Identificador de arquivo inválido.")
        base = self.base_dir.resolve()
        path = (base / exercise_id / key).resolve()
        if not str(path).startswith(str(base)):
            raise BudgetDocumentTypeNotAllowedError("Caminho de arquivo inválido.")
        if not path.is_file():
            from app.domain.services.planejamento_orcamentario.exceptions import (
                BudgetDocumentNotFoundError,
            )
            raise BudgetDocumentNotFoundError("Arquivo não encontrado.")
        return path
