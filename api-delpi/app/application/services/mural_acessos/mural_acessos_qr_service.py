"""QR do mural público — um código estável por mural."""

from __future__ import annotations

from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.config import settings

MURAL_ACESSOS_PUBLIC_PATH = "/p/mural-acessos/menu"
MURAL_ACESSOS_DEFAULT_PUBLIC_TOKEN = "mural"


def build_public_menu_path(public_token: str) -> str:
    return f"{MURAL_ACESSOS_PUBLIC_PATH}/{public_token}"


def build_public_menu_url(public_token: str) -> str:
    base = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    path = build_public_menu_path(public_token)
    return f"{base}{path}" if base else path


def render_public_menu_qr_png(public_token: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(build_public_menu_url(public_token))
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
