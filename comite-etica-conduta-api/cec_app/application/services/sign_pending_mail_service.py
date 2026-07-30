"""E-mail Outlook/Graph — aviso de assinatura pendente de ata do CEC."""

from __future__ import annotations

import html
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from cec_app.application.services.cec_mail_logo_attachment import (
    build_cec_logo_mail_attachment,
)
from cec_app.application.services.email_brand_layout_service import (
    BLUE_900,
    CecEmailBrandLayoutService,
    LOGO_CONTENT_ID,
)
from cec_app.config import settings
from cec_app.infrastructure.gateways.core_directory_service import CecCoreDirectoryService
from cec_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    MicrosoftGraphMailClient,
)

logger = logging.getLogger("comite_etica.mail")

_CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "pt-BR" / "mail.json"
)


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
    """Reutiliza credenciais Graph do Reports (Minha DELPI), com override CEC_*."""
    return MicrosoftGraphMailClient(
        tenant_id=settings.CEC_GRAPH_TENANT_ID,
        client_id=settings.CEC_GRAPH_CLIENT_ID,
        client_secret=settings.CEC_GRAPH_CLIENT_SECRET,
        sender=settings.CEC_GRAPH_MAIL_SENDER,
        recipient=None,
        timeout_seconds=float(settings.CEC_GRAPH_HTTP_TIMEOUT_SECONDS or "15"),
    )


class CecSignPendingMailService:
    def __init__(
        self,
        *,
        mail_client: MicrosoftGraphMailClient | None = None,
        directory: CecCoreDirectoryService | None = None,
        enabled: bool | None = None,
        public_base_url: str | None = None,
        logo_attachment: dict[str, Any] | None = None,
    ) -> None:
        self.mail = mail_client or build_graph_mail_client()
        self.directory = directory or CecCoreDirectoryService()
        self.enabled = settings.CEC_MAIL_ENABLED if enabled is None else enabled
        self.public_base_url = (
            public_base_url
            if public_base_url is not None
            else (settings.PUBLIC_BASE_URL or "")
        ).rstrip("/")
        self._logo_attachment = logo_attachment

    def _resolve_logo_attachment(self) -> dict[str, Any] | None:
        if self._logo_attachment is not None:
            return self._logo_attachment or None
        return build_cec_logo_mail_attachment()

    def _sign_url(self, minute_id: str) -> str:
        path = f"/apps/comite-etica-conduta/atas/{minute_id}/sign"
        if self.public_base_url:
            return f"{self.public_base_url}{path}"
        return path

    def build_subject(self, *, minute_number: str) -> str:
        tpl = str((_mail_content().get("signPending") or {}).get("subject") or "")
        return _format_template(tpl, minuteNumber=minute_number)

    def build_html(
        self,
        *,
        display_name: str,
        minute_number: str,
        title: str,
        minute_id: str,
        include_logo: bool = True,
    ) -> str:
        block = _mail_content().get("signPending") or {}
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
        footer_note = str(block.get("footerNote") or block.get("footer") or "")
        sign_url = self._sign_url(minute_id)

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

        return CecEmailBrandLayoutService.wrap(
            title=str(block.get("headerTitle") or "Comitê de Ética e Conduta"),
            subtitle=str(block.get("headerSubtitle") or "") or None,
            body_html=body,
            footer_site=str(block.get("footerSite") or "www.delpi.com.br"),
            footer_meta=str(
                block.get("footerMeta") or "Minha DELPI — Comitê de Ética e Conduta"
            ),
            logo_content_id=LOGO_CONTENT_ID if include_logo else None,
        )

    def notify_signers(
        self,
        *,
        signers: list[dict[str, Any]],
        minute_id: str,
        minute_number: str,
        title: str,
    ) -> int:
        """Envia e-mail a cada signatário com e-mail resolvido. Retorna qtd enviada."""
        if not self.enabled:
            return 0
        try:
            self.mail.ensure_auth_configured()
        except GraphMailError:
            logger.warning("cec_mail_skipped_graph_not_configured")
            return 0

        user_ids = [str(item.get("user_id") or "") for item in signers]
        emails_by_user = self.directory.lookup_emails_by_user_ids(user_ids)
        if not emails_by_user:
            logger.warning("cec_mail_skipped_no_recipient_emails minute=%s", minute_id)
            return 0

        logo = self._resolve_logo_attachment()
        attachments = [logo] if logo else None
        subject = self.build_subject(minute_number=minute_number)
        sent = 0
        for signer in signers:
            user_id = str(signer.get("user_id") or "").strip()
            email = emails_by_user.get(user_id)
            if not email:
                logger.warning(
                    "cec_mail_signer_without_email user=%s minute=%s",
                    user_id,
                    minute_id,
                )
                continue
            display_name = str(signer.get("display_name") or "").strip() or "colegado"
            html_body = self.build_html(
                display_name=display_name,
                minute_number=minute_number,
                title=title,
                minute_id=minute_id,
                include_logo=bool(logo),
            )
            try:
                self.mail.send_mail_to(
                    subject=subject,
                    html_body=html_body,
                    to_addresses=[email],
                    attachments=attachments,
                )
                sent += 1
            except GraphMailError as exc:
                logger.warning(
                    "cec_mail_send_failed user=%s minute=%s error=%s",
                    user_id,
                    minute_id,
                    str(exc)[:200],
                )
            except Exception:
                logger.exception(
                    "cec_mail_send_unexpected user=%s minute=%s",
                    user_id,
                    minute_id,
                )
        return sent
