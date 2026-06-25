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
    "image/gif",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_EVIDENCE_BYTES = 25 * 1024 * 1024


class PacEvidenceStorageError(ValueError):
    pass


class PacEvidenceStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.PAC_EVIDENCE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise PacEvidenceStorageError("Arquivo vazio.")
        if size_bytes > MAX_EVIDENCE_BYTES:
            raise PacEvidenceStorageError("Arquivo excede o limite de 25 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise PacEvidenceStorageError(
                "Formato inválido. Use imagem, PDF, planilha ou documento de texto."
            )

    def save(
        self,
        *,
        plan_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"

        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / plan_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name

    def resolve_file(self, *, plan_id: str, stored_name: str) -> Path:
        path = (self.base_dir / plan_id / stored_name).resolve()
        base = self.base_dir.resolve()
        if not str(path).startswith(str(base)):
            raise PacEvidenceStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise PacEvidenceStorageError("Arquivo não encontrado.")
        return path

    def delete_file(self, *, plan_id: str, stored_name: str) -> None:
        path = self.resolve_file(plan_id=plan_id, stored_name=stored_name)
        path.unlink(missing_ok=True)
