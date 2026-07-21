"""Anexo inline (CID) da logo Delpi para e-mails Reports."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from app.domain.services.reports.report_email_brand_layout_service import (
    LOGO_CONTENT_ID,
)
from app.domain.services.reports.report_types import ReportAttachment

_ASSETS_DIR = Path(__file__).resolve().parents[1] / "pdf" / "assets"
_LOGO_PNG = _ASSETS_DIR / "logo_delpi.png"


@lru_cache(maxsize=1)
def build_delpi_logo_report_attachment() -> ReportAttachment:
    """Carrega ``logo_delpi.png`` como anexo Graph inline (``cid:delpi-logo``)."""
    raw = _LOGO_PNG.read_bytes()
    return ReportAttachment(
        name="logo_delpi.png",
        content_type="image/png",
        content_base64=base64.b64encode(raw).decode("ascii"),
        is_inline=True,
        content_id=LOGO_CONTENT_ID,
    )
