from __future__ import annotations

import re
import uuid
from pathlib import Path

from cipa_app.config import settings

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class CipaStorageError(ValueError):
    """Erro de validação de arquivo CIPA."""


class SignatureStorageService:
    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CIPA_SIGNATURE_UPLOAD_DIR)
        self.max_bytes = max_bytes or settings.CIPA_SIGNATURE_MAX_BYTES

    def save_png(self, *, unit_code: str, minute_id: str, raw: bytes) -> str:
        if not raw:
            raise CipaStorageError("Assinatura vazia.")
        if len(raw) > self.max_bytes:
            raise CipaStorageError("Assinatura excede o tamanho máximo permitido.")
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise CipaStorageError("Formato de assinatura inválido. Envie uma imagem PNG.")

        folder = self.base_dir / unit_code / minute_id
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        path = folder / filename
        path.write_bytes(raw)
        return str(path)


class AttachmentStorageService:
    ALLOWED_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CIPA_ATTACHMENT_UPLOAD_DIR)
        self.max_bytes = max_bytes or settings.CIPA_ATTACHMENT_MAX_BYTES

    def save(
        self,
        *,
        unit_code: str,
        minute_id: str,
        file_name: str,
        content_type: str,
        raw: bytes,
    ) -> str:
        if content_type not in self.ALLOWED_TYPES:
            raise CipaStorageError("Tipo de anexo não permitido.")
        if len(raw) > self.max_bytes:
            raise CipaStorageError("Anexo excede o tamanho máximo permitido.")
        safe = _SAFE_NAME_RE.sub("_", file_name).strip("._") or "file"
        folder = self.base_dir / unit_code / minute_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{uuid.uuid4()}_{safe}"
        path.write_bytes(raw)
        return str(path)


class PdfStorageService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CIPA_PDF_UPLOAD_DIR)

    def save(self, *, unit_code: str, minute_id: str, raw: bytes) -> str:
        folder = self.base_dir / unit_code / minute_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "final.pdf"
        path.write_bytes(raw)
        return str(path)

    def read(self, path: str) -> bytes:
        file_path = Path(path)
        if not file_path.is_file():
            raise CipaStorageError("Arquivo PDF não encontrado.")
        return file_path.read_bytes()
