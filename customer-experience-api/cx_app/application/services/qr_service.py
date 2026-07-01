from __future__ import annotations

from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from cx_app.config import settings


def _public_url(token: str, path: str) -> str:
    base = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    normalized = "/" + path.strip("/")
    return f"{base}{normalized}/{token}"


def build_public_url(token: str) -> str:
    """URL pública da página de agradecimento (QR de congratulação)."""
    return _public_url(token, settings.CX_PUBLIC_WELCOME_PATH)


def build_form_url(token: str) -> str:
    """URL pública de um formulário personalizável (estilo Google Forms)."""
    return _public_url(token, settings.CX_PUBLIC_FORM_PATH)


class QrService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CX_QR_DIR)

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

    def _write(self, *, url: str, stored_name: str) -> str:
        self._ensure_dir()
        (self.base_dir / stored_name).write_bytes(self.render_png(url))
        return stored_name

    def generate(self, *, token: str) -> str:
        """QR da página de agradecimento. Retorna o nome do arquivo."""
        return self._write(url=build_public_url(token), stored_name=f"{token}.png")

    def generate_form(self, *, token: str) -> str:
        """QR de um formulário personalizável. Retorna o nome do arquivo."""
        return self._write(url=build_form_url(token), stored_name=f"form-{token}.png")

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
