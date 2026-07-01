from __future__ import annotations

import uuid
from pathlib import Path

from cx_app.config import settings

# Whitelist de imagens aceitas para foto do participante.
_ALLOWED_MIME_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class PhotoValidationError(ValueError):
    """Foto inválida (tipo não suportado ou tamanho excedido)."""


class PhotoStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CX_PHOTO_UPLOAD_DIR)

    def _ensure_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, *, content: bytes, mime_type: str | None) -> str:
        normalized = (mime_type or "").split(";", 1)[0].strip().lower()
        if normalized not in _ALLOWED_MIME_EXT:
            raise PhotoValidationError(
                "Formato de imagem não suportado. Envie JPG, PNG ou WEBP."
            )
        if not content:
            raise PhotoValidationError("Arquivo de foto vazio.")
        if len(content) > settings.CX_MAX_PHOTO_BYTES:
            limit_mb = settings.CX_MAX_PHOTO_BYTES // (1024 * 1024)
            raise PhotoValidationError(f"Foto acima do limite de {limit_mb} MB.")
        return normalized

    def save(self, *, content: bytes, mime_type: str | None) -> tuple[str, str]:
        normalized = self.validate(content=content, mime_type=mime_type)
        self._ensure_dir()
        stored_name = f"{uuid.uuid4().hex}{_ALLOWED_MIME_EXT[normalized]}"
        (self.base_dir / stored_name).write_bytes(content)
        return stored_name, normalized

    def read(self, filename: str) -> bytes | None:
        target = self.base_dir / filename
        if not target.is_file():
            return None
        return target.read_bytes()

    def delete(self, filename: str | None) -> None:
        if not filename:
            return
        target = self.base_dir / filename
        if target.is_file():
            target.unlink()
