from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from tm_app.config import settings

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
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024


class InteractionAttachmentStorage:
    """Binário da sala no volume do Transformômetro. Metadado fica no Postgres."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TM_INTERACTION_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, room_id: str, original_name: str, content: bytes, mime_type: str | None) -> tuple[str, str]:
        size = len(content)
        if size <= 0:
            raise ValueError("Arquivo vazio.")
        if size > MAX_ATTACHMENT_BYTES:
            raise ValueError("Arquivo excede o limite de 25 MB.")
        normalized = (mime_type or "").split(";")[0].strip().lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise ValueError("Formato inválido. Use imagem, PDF, planilha ou documento de texto.")
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(normalized) or ".bin"
        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / room_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / stored_name).write_bytes(content)
        safe_name = Path(original_name).name.strip() or stored_name
        return stored_name, safe_name[:180]

    def resolve_file(self, *, room_id: str, stored_name: str) -> Path:
        base = self.base_dir.resolve()
        path = (self.base_dir / room_id / Path(stored_name).name).resolve()
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise ValueError("Caminho de arquivo inválido.") from exc
        if not path.is_file():
            raise ValueError("Arquivo não encontrado.")
        return path
