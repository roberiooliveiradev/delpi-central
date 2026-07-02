from __future__ import annotations

import uuid
from pathlib import Path

from app.config import settings


class QualityLabelsCertificateStorage:
    """Persiste o PDF imutável do Certificado de Qualidade emitido."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.QUALITY_LABELS_CERTIFICATE_DIR)

    def _ensure_dir(self, sub: str) -> Path:
        target = self.base_dir / sub
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _resolve(self, filename: str) -> Path:
        target = (self.base_dir / filename).resolve()
        base = self.base_dir.resolve()
        if base not in target.parents and target != base:
            raise ValueError("Caminho de certificado inválido.")
        return target

    def save(self, *, certificate_id: str, content: bytes) -> str:
        folder = self._ensure_dir(certificate_id)
        stored_name = f"{certificate_id}/{uuid.uuid4().hex}.pdf"
        (folder / Path(stored_name).name).write_bytes(content)
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
