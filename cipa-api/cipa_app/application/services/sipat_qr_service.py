from __future__ import annotations

from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from cipa_app.config import settings


def build_sipat_public_url(token: str) -> str:
    base = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    path = "/" + settings.CIPA_PUBLIC_SIPAT_PATH.strip("/")
    return f"{base}{path}/{token}"


class SipatQrService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CIPA_SIPAT_QR_DIR)

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
        from io import BytesIO

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def generate(self, *, token: str) -> str:
        self._ensure_dir()
        filename = f"sipat-{token}.png"
        url = build_sipat_public_url(token)
        (self.base_dir / filename).write_bytes(self.render_png(url))
        return filename

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
