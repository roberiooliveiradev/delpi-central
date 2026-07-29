"""Storage de assinaturas e PDF das atas Transforma+."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from tm_app.config import settings

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class TmAtaStorageError(ValueError):
    """Erro de validação de arquivo de ata."""


class SignatureStorageService:
    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TM_ATA_SIGNATURE_UPLOAD_DIR)
        self.max_bytes = max_bytes or settings.TM_ATA_SIGNATURE_MAX_BYTES

    def save_png(self, *, unit_code: str, minute_id: str, raw: bytes) -> str:
        if not raw:
            raise TmAtaStorageError("Assinatura vazia.")
        if len(raw) > self.max_bytes:
            raise TmAtaStorageError("Assinatura excede o tamanho máximo permitido.")
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise TmAtaStorageError("Formato de assinatura inválido. Envie uma imagem PNG.")

        folder = self.base_dir / unit_code / minute_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{uuid.uuid4()}.png"
        path.write_bytes(raw)
        return str(path)

    def read(self, path: str) -> bytes:
        base = self.base_dir.resolve()
        file_path = Path(path).resolve()
        try:
            file_path.relative_to(base)
        except ValueError as exc:
            raise TmAtaStorageError("Caminho de assinatura inválido.") from exc
        if not file_path.is_file():
            raise TmAtaStorageError("Imagem de assinatura não encontrada.")
        return file_path.read_bytes()


class UserSignatureStorageService:
    """Assinatura pessoal estável por usuário (sobrescreve no update)."""

    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TM_ATA_SIGNATURE_UPLOAD_DIR) / "profiles"
        self.max_bytes = max_bytes or settings.TM_ATA_SIGNATURE_MAX_BYTES

    def _path_for(self, user_id: str) -> Path:
        safe_id = _SAFE_NAME_RE.sub("_", (user_id or "").strip()) or "unknown"
        return self.base_dir / f"{safe_id}.png"

    def exists(self, user_id: str) -> bool:
        return self._path_for(user_id).is_file()

    def save_png(self, *, user_id: str, raw: bytes) -> str:
        if not raw:
            raise TmAtaStorageError("Assinatura vazia.")
        if len(raw) > self.max_bytes:
            raise TmAtaStorageError("Assinatura excede o tamanho máximo permitido.")
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise TmAtaStorageError("Formato de assinatura inválido. Envie uma imagem PNG.")

        self.base_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(user_id)
        path.write_bytes(raw)
        return str(path)

    def read(self, user_id: str) -> bytes:
        path = self._path_for(user_id)
        if not path.is_file():
            raise TmAtaStorageError("Assinatura pessoal não encontrada.")
        return path.read_bytes()


class PdfStorageService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TM_ATA_PDF_UPLOAD_DIR)

    def save(self, *, unit_code: str, minute_id: str, raw: bytes) -> str:
        folder = self.base_dir / unit_code / minute_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "final.pdf"
        path.write_bytes(raw)
        return str(path)

    def read(self, path: str) -> bytes:
        file_path = Path(path)
        if not file_path.is_file():
            raise TmAtaStorageError("Arquivo PDF não encontrado.")
        return file_path.read_bytes()
