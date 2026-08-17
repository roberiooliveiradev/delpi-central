"""E-mail Outlook/Graph — aviso de assinatura pendente (magic link)."""

from __future__ import annotations

import html
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from tm_app.application.services.tm_email_brand_layout_service import (
    BLUE_900,
    TmEmailBrandLayoutService,
)
from tm_app.config import settings
from tm_app.infrastructure.gateways.core_directory_service import TmCoreDirectoryService
from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    MicrosoftGraphMailClient,
)

logger = logging.getLogger("transformometro.mail")

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "pt-BR" / "mail.json"


@lru_cache(maxsize=1)
def _mail_content() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload if isinstance(payload, dict) else {}


def _format_template(template: str, **kwargs: str) -> str:
    text = template
    for key, value in kwargs.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def build_graph_mail_client() -> MicrosoftGraphMailClient:
    return MicrosoftGraphMailClient(
        tenant_id=settings.TM_GRAPH_TENANT_ID,
        client_id=settings.TM_GRAPH_CLIENT_ID,
        client_secret=settings.TM_GRAPH_CLIENT_SECRET,
        sender=settings.TM_GRAPH_MAIL_SENDER,
        recipient=None,
        timeout_seconds=float(settings.TM_GRAPH_HTTP_TIMEOUT_SECONDS or "15"),
    )


class TmSignPendingMailService:
    def __init__(
        self,
        *,
        mail_client: MicrosoftGraphMailClient | None = None,
        directory: TmCoreDirectoryService | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.mail = mail_client or build_graph_mail_client()
        self.directory = directory or TmCoreDirectoryService()
        self.enabled = settings.TM_MAIL_ENABLED if enabled is None else enabled

    def _template_block(self, template_key: str) -> dict[str, Any]:
        content = _mail_content()
        block = content.get(template_key) or content.get("signPending") or {}
        return block if isinstance(block, dict) else {}

    def build_subject(self, *, minute_number: str, template_key: str = "signPending") -> str:
        tpl = str(self._template_block(template_key).get("subject") or "")
        return _format_template(tpl, minuteNumber=minute_number)

    def build_html(
        self,
        *,
        display_name: str,
        minute_number: str,
        title: str,
        sign_url: str,
        template_key: str = "signPending",
    ) -> str:
        block = self._template_block(template_key)
        greeting = _format_template(
            str(block.get("greeting") or ""),
            displayName=display_name or "colegado",
        )
        intro = _format_template(
            str(block.get("intro") or ""),
            minuteNumber=minute_number,
            title=title,
        )
        cta = str(block.get("ctaLabel") or "Assinar ata")
        footer_note = str(block.get("footerNote") or "")

        body = (
            f'<p style="margin:0 0 14px 0;font-size:15px;color:#1A202C;">'
            f"{html.escape(greeting)}</p>"
            f'<p style="margin:0 0 20px 0;font-size:14px;line-height:1.55;color:#1A202C;">'
            f"{html.escape(intro)}</p>"
            f'<p style="margin:0 0 18px 0;">'
            f'<a href="{html.escape(sign_url, quote=True)}" '
            f'style="display:inline-block;background:{BLUE_900};color:#ffffff;'
            f"text-decoration:none;padding:12px 18px;border-radius:4px;"
            f'font-size:14px;font-weight:700;">{html.escape(cta)}</a></p>'
            f'<p style="margin:0;font-size:12px;color:#64748B;line-height:1.45;">'
            f"{html.escape(footer_note)}</p>"
        )

        return TmEmailBrandLayoutService.wrap(
            title=str(block.get("headerTitle") or "Transformômetro"),
            subtitle=str(block.get("headerSubtitle") or "") or None,
            body_html=body,
            footer_site=str(block.get("footerSite") or "www.delpi.com.br"),
            footer_meta=str(
                block.get("footerMeta") or "Minha DELPI — Transformômetro"
            ),
            logo_content_id=None,
        )

    def notify_signers(
        self,
        *,
        signers: list[dict[str, Any]],
        minute_number: str,
        title: str,
        template_key: str = "signPending",
    ) -> int:
        """Envia e-mail com CTA = magic link (`sign_url` por signer). Retorna qtd enviada."""
        if not self.enabled:
            return 0
        try:
            self.mail.ensure_auth_configured()
        except GraphMailError:
            logger.warning("tm_mail_skipped_graph_not_configured")
            return 0

        user_ids = [
            str(item.get("user_id") or "").strip()
            for item in signers
            if str(item.get("user_id") or "").strip()
        ]
        emails_by_user = (
            self.directory.lookup_emails_by_user_ids(user_ids) if user_ids else {}
        )

        subject = self.build_subject(
            minute_number=minute_number, template_key=template_key
        )
        sent = 0
        for signer in signers:
            user_id = str(signer.get("user_id") or "").strip()
            invite_email = str(signer.get("invite_email") or "").strip()
            email = emails_by_user.get(user_id) if user_id else None
            if not email and invite_email and "@" in invite_email:
                email = invite_email
            if not email:
                logger.warning(
                    "tm_mail_signer_without_email user=%s minute_signer=%s",
                    user_id or "-",
                    signer.get("id"),
                )
                continue
            sign_url = str(signer.get("sign_url") or "").strip()
            if not sign_url:
                logger.warning(
                    "tm_mail_signer_without_sign_url signer=%s",
                    signer.get("id"),
                )
                continue
            display_name = str(signer.get("display_name") or "").strip() or "colegado"
            html_body = self.build_html(
                display_name=display_name,
                minute_number=minute_number,
                title=title,
                sign_url=sign_url,
                template_key=template_key,
            )
            try:
                self.mail.send_mail_to(
                    subject=subject,
                    html_body=html_body,
                    to_addresses=[email],
                )
                sent += 1
            except GraphMailError as exc:
                logger.warning(
                    "tm_mail_send_failed email=%s error=%s",
                    email,
                    str(exc)[:200],
                )
            except Exception:
                logger.exception("tm_mail_send_unexpected email=%s", email)
        return sent
