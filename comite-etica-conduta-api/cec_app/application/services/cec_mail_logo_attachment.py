"""Anexo inline (CID) do emblema do Comitê para e-mails Outlook/Graph."""

from __future__ import annotations

import base64
import io
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image as PillowImage

from cec_app.application.services.email_brand_layout_service import LOGO_CONTENT_ID

_LOGO_PATH = (
    Path(__file__).resolve().parents[2]
    / "infrastructure"
    / "pdf"
    / "assets"
    / "logo-comite_etica.png"
)
_EMAIL_LOGO_MAX_PX = 144


@lru_cache(maxsize=1)
def build_cec_logo_mail_attachment() -> dict[str, Any] | None:
    """Redimensiona o emblema e monta anexo Graph inline ``cid:cec-logo``."""
    if not _LOGO_PATH.is_file():
        return None
    try:
        with PillowImage.open(_LOGO_PATH) as src:
            img = src.convert("RGBA")
            img.thumbnail((_EMAIL_LOGO_MAX_PX, _EMAIL_LOGO_MAX_PX), PillowImage.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
    except OSError:
        return None

    return {
        "name": "logo-comite-etica.png",
        "content_type": "image/png",
        "content_base64": base64.b64encode(buf.getvalue()).decode("ascii"),
        "is_inline": True,
        "content_id": LOGO_CONTENT_ID,
    }
