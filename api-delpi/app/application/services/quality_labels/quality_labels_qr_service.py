from __future__ import annotations

from io import BytesIO
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.config import settings

# Página pública servida pelo public-hub (app quality-labels, view inspection).
QUALITY_LABELS_PUBLIC_PATH = "/p/quality-labels/inspection"


def build_public_url(token: str) -> str:
    base = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    return f"{base}{QUALITY_LABELS_PUBLIC_PATH}/{token}"


class QualityLabelsQrService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.QUALITY_LABELS_QR_DIR)

    def _ensure_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def render_png(self, url: str) -> bytes:
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def generate(self, *, token: str) -> str:
        """Gera e persiste o PNG do QR. Retorna o nome do arquivo."""
        self._ensure_dir()
        stored_name = f"{token}.png"
        (self.base_dir / stored_name).write_bytes(self.render_png(build_public_url(token)))
        return stored_name

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
