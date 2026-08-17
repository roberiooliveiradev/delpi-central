# app/application/services/notification_email_service.py

from __future__ import annotations

import html
import logging
import os
from typing import Any, Protocol
from urllib.parse import quote

logger = logging.getLogger(__name__)

_SEVERITY_LABEL = {
    "info": "Aviso",
    "success": "Sucesso",
    "warning": "Atenção",
    "error": "Alerta",
}


def notification_mail_enabled() -> bool:
    raw = (os.getenv("CORE_NOTIFICATION_MAIL_ENABLED") or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def build_notification_email_html(
    *,
    title: str | None,
    message: str,
    notification_type: str,
    application_name: str | None,
    portal_base_url: str,
) -> tuple[str, str]:
    severity = _SEVERITY_LABEL.get((notification_type or "info").strip().lower(), "Aviso")
    plain_title = (title or "").strip() or "Notificação Minha DELPI"
    safe_title = html.escape(plain_title)
    safe_message = html.escape((message or "").strip())
    safe_app = html.escape((application_name or "Minha DELPI").strip())
    link = portal_base_url.rstrip("/") + "/notifications"
    subject_prefix = "[Alerta]" if (notification_type or "").lower() == "error" else "[Minha DELPI]"
    subject = f"{subject_prefix} {plain_title}"
    body = f"""<!DOCTYPE html>
<html><body style="font-family:Segoe UI,Arial,sans-serif;color:#111;line-height:1.45">
  <p style="margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#666">{severity}</p>
  <h1 style="margin:0 0 12px;font-size:20px">{safe_title}</h1>
  <p style="margin:0 0 16px">{safe_message}</p>
  <p style="margin:0 0 20px;color:#555;font-size:13px">Origem: {safe_app}</p>
  <p><a href="{html.escape(link)}" style="display:inline-block;padding:10px 14px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px">Abrir na Minha DELPI</a></p>
  <p style="margin-top:24px;font-size:12px;color:#777">Você recebeu este e-mail porque marcou a categoria como importante ou ativou receber por e-mail. Preferências: {html.escape(link)}</p>
</body></html>"""
    return subject, body


class NotificationMailSender(Protocol):
    def send_mail_to(
        self,
        *,
        subject: str,
        html_body: str,
        to_addresses: list[str],
    ) -> Any: ...


def build_notification_graph_mail_client() -> NotificationMailSender:
    from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
        MicrosoftGraphMailClient,
    )

    return MicrosoftGraphMailClient(
        tenant_id=os.getenv("GRAPH_REPORTS_TENANT_ID") or os.getenv("GRAPH_TENANT_ID"),
        client_id=os.getenv("GRAPH_REPORTS_CLIENT_ID") or os.getenv("GRAPH_CLIENT_ID"),
        client_secret=os.getenv("GRAPH_REPORTS_CLIENT_SECRET")
        or os.getenv("GRAPH_CLIENT_SECRET"),
        sender=os.getenv("GRAPH_REPORTS_MAIL_SENDER")
        or os.getenv("CORE_NOTIFICATION_MAIL_SENDER")
        or "minhadelpi@delpi.com.br",
    )


class NotificationEmailService:
    """Best-effort e-mail after notification create — never raises to callers."""

    def __init__(self, mail_client: NotificationMailSender | None = None):
        self._mail = mail_client

    def send_if_enabled(
        self,
        *,
        to_email: str | None,
        title: str | None,
        message: str,
        notification_type: str,
        application_name: str | None = None,
    ) -> bool:
        if not notification_mail_enabled():
            return False
        recipient = (to_email or "").strip()
        if not recipient or "@" not in recipient:
            return False

        portal_base = (
            os.getenv("CORE_NOTIFICATION_PORTAL_BASE_URL")
            or os.getenv("PORTAL_PUBLIC_URL")
            or "https://minhadelpi.delpi.com.br"
        ).strip()
        subject, html_body = build_notification_email_html(
            title=title,
            message=message,
            notification_type=notification_type,
            application_name=application_name,
            portal_base_url=portal_base,
        )
        try:
            from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
                GraphMailError,
            )

            client = self._mail or build_notification_graph_mail_client()
            client.send_mail_to(
                subject=subject,
                html_body=html_body,
                to_addresses=[recipient],
            )
            return True
        except Exception as exc:
            # GraphMailError is a subclass of Exception; avoid import at module load.
            err_name = type(exc).__name__
            if err_name == "GraphMailError":
                logger.warning(
                    "notification_email_failed recipient=%s err=%s",
                    recipient,
                    quote(str(exc), safe=""),
                )
                return False
            logger.exception("notification_email_unexpected_error recipient=%s", recipient)
            return False
