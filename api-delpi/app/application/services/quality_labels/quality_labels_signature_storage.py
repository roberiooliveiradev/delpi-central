from __future__ import annotations

import uuid
from pathlib import Path

from app.config import settings

# Assinatura do inspetor. Aceita apenas PNG (canvas exporta PNG; upload é
# normalizado no frontend). Limite conservador — assinatura é uma imagem pequena.
_ALLOWED_MIME = {"image/png"}
_MAX_BYTES = 3 * 1024 * 1024


class QualityLabelsSignatureError(ValueError):
    """Erro de validação da assinatura do inspetor."""


class QualityLabelsSignatureStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.QUALITY_LABELS_SIGNATURE_DIR)

    def _ensure_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, filename: str) -> Path:
        target = (self.base_dir / filename).resolve()
        base = self.base_dir.resolve()
        if base not in target.parents and target != base:
            raise QualityLabelsSignatureError("Caminho de assinatura inválido.")
        return target

    def save(self, *, content: bytes, mime_type: str | None) -> str:
        normalized = (mime_type or "").split(";")[0].strip().lower()
        if normalized not in _ALLOWED_MIME:
            raise QualityLabelsSignatureError(
                "Formato de assinatura inválido. Envie uma imagem PNG."
            )
        if not content:
            raise QualityLabelsSignatureError("Assinatura vazia.")
        if len(content) > _MAX_BYTES:
            raise QualityLabelsSignatureError("Assinatura excede o tamanho máximo (3 MB).")

        self._ensure_dir()
        stored_name = f"{uuid.uuid4().hex}.png"
        self._resolve(stored_name).write_bytes(content)
        return stored_name

    def read(self, filename: str | None) -> bytes | None:
        if not filename:
            return None
        target = self._resolve(filename)
        if not target.is_file():
            return None
        return target.read_bytes()

    def delete(self, filename: str | None) -> None:
        if not filename:
            return
        target = self._resolve(filename)
        if target.is_file():
            target.unlink()
