from __future__ import annotations

import uuid
from pathlib import Path

from tv_app.application.services.tv_dashboard_content_service import (
    media_setting_int,
    media_setting_mime_ext,
)
from tv_app.config import settings


class MediaValidationError(ValueError):
    """Arquivo de mídia inválido (tipo ou tamanho)."""


class MediaStorageService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TV_DASHBOARD_MEDIA_UPLOAD_DIR)

    def _ensure_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _mime_map(self, media_kind: str) -> dict[str, str]:
        return media_setting_mime_ext(media_kind)

    def _max_bytes(self, media_kind: str) -> int:
        if media_kind == "video":
            return media_setting_int("maxVideoBytes", 100 * 1024 * 1024)
        return media_setting_int("maxImageBytes", 10 * 1024 * 1024)

    def detect_kind(self, mime_type: str | None) -> str | None:
        normalized = (mime_type or "").split(";", 1)[0].strip().lower()
        if normalized in self._mime_map("image"):
            return "image"
        if normalized in self._mime_map("video"):
            return "video"
        return None

    def validate(self, *, content: bytes, mime_type: str | None) -> tuple[str, str]:
        kind = self.detect_kind(mime_type)
        if not kind:
            raise MediaValidationError(
                "Formato não suportado. Envie JPG, PNG, WEBP, GIF, MP4 ou WEBM."
            )
        if not content:
            raise MediaValidationError("Arquivo vazio.")
        max_bytes = self._max_bytes(kind)
        if len(content) > max_bytes:
            limit_mb = max(1, max_bytes // (1024 * 1024))
            raise MediaValidationError(f"Arquivo acima do limite de {limit_mb} MB.")
        normalized = (mime_type or "").split(";", 1)[0].strip().lower()
        return kind, normalized

    def save(self, *, content: bytes, mime_type: str | None) -> tuple[str, str, str]:
        kind, normalized = self.validate(content=content, mime_type=mime_type)
        ext = self._mime_map(kind)[normalized]
        self._ensure_dir()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        (self.base_dir / stored_name).write_bytes(content)
        return stored_name, normalized, kind

    def read(self, stored_name: str) -> bytes | None:
        target = self.base_dir / stored_name
        if not target.is_file():
            return None
        return target.read_bytes()

    def delete(self, stored_name: str | None) -> None:
        if not stored_name:
            return
        target = self.base_dir / stored_name
        if target.is_file():
            target.unlink()
