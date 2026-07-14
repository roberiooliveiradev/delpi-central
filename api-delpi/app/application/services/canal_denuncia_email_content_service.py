"""Montagem do e-mail de denúncia anônima (sem dados de identidade)."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any


EMAIL_SUBJECT = "Nova denúncia recebida pelo Canal de Denúncia"


def format_received_at(created_at: Any) -> str:
    if isinstance(created_at, datetime):
        formatted = created_at.strftime("%d/%m/%Y %H:%M:%S %Z").strip()
        return formatted or created_at.isoformat()
    text = str(created_at or "").strip()
    if not text:
        return "—"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        formatted = parsed.strftime("%d/%m/%Y %H:%M:%S %Z").strip()
        return formatted or parsed.isoformat()
    except ValueError:
        return text


def build_denuncia_email_html(*, description: str, created_at: Any) -> str:
    safe_description = html.escape((description or "").strip(), quote=True)
    safe_created = html.escape(format_received_at(created_at), quote=True)
    return (
        "<p>Uma nova denúncia anônima foi recebida pelo Canal de Denúncia da Minha DELPI.</p>"
        f"<p><strong>Data de recebimento:</strong> {safe_created}</p>"
        "<p><strong>Relato:</strong></p>"
        f"<p>{safe_description.replace(chr(10), '<br>')}</p>"
    )
