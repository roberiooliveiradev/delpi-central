from __future__ import annotations

from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from tv_app.config import settings


def build_public_presentation_url(public_token: str) -> str:
    base = (settings.PUBLIC_BASE_URL or "http://localhost").rstrip("/")
    path = settings.TV_DASHBOARD_PUBLIC_PATH.rstrip("/")
    return f"{base}{path}/{public_token}"


def render_qr_png(url: str) -> bytes:
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
