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
MAX_ARQUIVO_BYTES = 25 * 1024 * 1024


class ProcessoArquivoStorageError(ValueError):
    pass


class ProcessoArquivoStorage:
    """Storage persistente de arquivos do processo-mestre (metadado no Postgres + binário no volume)."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TM_PROCESSO_ARQUIVO_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise ProcessoArquivoStorageError("Arquivo vazio.")
        if size_bytes > MAX_ARQUIVO_BYTES:
            raise ProcessoArquivoStorageError("Arquivo excede o limite de 25 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise ProcessoArquivoStorageError(
                "Formato inválido. Use imagem, PDF, planilha ou documento de texto."
            )

    def save(
        self,
        *,
        processo_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"

        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / processo_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / stored_name).write_bytes(content)
        return stored_name

    def resolve_file(self, *, processo_id: str, stored_name: str) -> Path:
        normalized_name = (stored_name or "").strip()
        if not normalized_name:
            raise ProcessoArquivoStorageError("Arquivo não encontrado.")

        base = self.base_dir.resolve()
        path = (self.base_dir / (processo_id or "").strip() / normalized_name).resolve()
        if not str(path).startswith(str(base)):
            raise ProcessoArquivoStorageError("Caminho de arquivo inválido.")
        if path.is_file():
            return path
        raise ProcessoArquivoStorageError("Arquivo não encontrado.")

    def delete_file(self, *, processo_id: str, stored_name: str) -> None:
        try:
            path = self.resolve_file(processo_id=processo_id, stored_name=stored_name)
        except ProcessoArquivoStorageError:
            return
        path.unlink(missing_ok=True)
