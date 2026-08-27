"""E-mail Outlook/Graph — aviso de assinatura pendente (magic link)."""

from __future__ import annotations

import html
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from tm_app.application.services.tm_email_brand_layout_service import (
    BLUE_900,
    TmEmailBrandLayoutService,
)
from tm_app.config import settings
from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_NOT_APPLICABLE,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_FAILED,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
    MAIL_SEND_SKIPPED_MAIL_DISABLED,
    MAIL_SEND_SKIPPED_NO_EMAIL,
)
from tm_app.infrastructure.gateways.core_directory_service import TmCoreDirectoryService
from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    MicrosoftGraphMailClient,
)

logger = logging.getLogger("transformometro.mail")


@dataclass(frozen=True)
class SignInviteMailResult:
    invite_id: str
    signer_id: str | None
    mail_template_key: str
    mail_recipient: str | None
    mail_send_status: str
    mail_delivery_status: str
    mail_last_error: str | None = None


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
        invite_id: str | None = None,
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

        invite_marker = ""
        if invite_id:
            invite_marker = (
                f"<!-- X-Delpi-Invite-Id: {html.escape(str(invite_id).strip())} -->\n"
            )

        body = (
            invite_marker
            + f'<p style="margin:0 0 14px 0;font-size:15px;color:#1A202C;">'
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

    def _result(
        self,
        *,
        signer: dict[str, Any],
        template_key: str,
        mail_send_status: str,
        mail_delivery_status: str,
        mail_recipient: str | None = None,
        mail_last_error: str | None = None,
    ) -> SignInviteMailResult:
        invite_id = str(signer.get("invite_id") or "").strip()
        signer_id = str(signer.get("id") or "").strip() or None
        return SignInviteMailResult(
            invite_id=invite_id,
            signer_id=signer_id,
            mail_template_key=template_key,
            mail_recipient=mail_recipient,
            mail_send_status=mail_send_status,
            mail_delivery_status=mail_delivery_status,
            mail_last_error=mail_last_error,
        )

    def notify_signers(
        self,
        *,
        signers: list[dict[str, Any]],
        minute_number: str,
        title: str,
        template_key: str = "signPending",
    ) -> list[SignInviteMailResult]:
        """Envia e-mail com CTA = magic link (`sign_url` por signer)."""
        if not signers:
            return []

        if not self.enabled:
            return [
                self._result(
                    signer=signer,
                    template_key=template_key,
                    mail_send_status=MAIL_SEND_SKIPPED_MAIL_DISABLED,
                    mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                )
                for signer in signers
            ]

        try:
            self.mail.ensure_auth_configured()
        except GraphMailError as exc:
            logger.warning("tm_mail_skipped_graph_not_configured")
            return [
                self._result(
                    signer=signer,
                    template_key=template_key,
                    mail_send_status=MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
                    mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                    mail_last_error=str(exc)[:480] or None,
                )
                for signer in signers
            ]

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
        results: list[SignInviteMailResult] = []
        for signer in signers:
            user_id = str(signer.get("user_id") or "").strip()
            invite_email = str(signer.get("invite_email") or "").strip()
            email = emails_by_user.get(user_id) if user_id else None
            if not email and invite_email and "@" in invite_email:
                email = invite_email
            sign_url = str(signer.get("sign_url") or "").strip()
            invite_id = str(signer.get("invite_id") or "").strip()
            if not email:
                logger.warning(
                    "tm_mail_signer_without_email user=%s minute_signer=%s",
                    user_id or "-",
                    signer.get("id"),
                )
                results.append(
                    self._result(
                        signer=signer,
                        template_key=template_key,
                        mail_send_status=MAIL_SEND_SKIPPED_NO_EMAIL,
                        mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                    )
                )
                continue
            if not sign_url:
                logger.warning(
                    "tm_mail_signer_without_sign_url signer=%s",
                    signer.get("id"),
                )
                results.append(
                    self._result(
                        signer=signer,
                        template_key=template_key,
                        mail_send_status=MAIL_SEND_FAILED,
                        mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                        mail_last_error="sign_url ausente",
                    )
                )
                continue
            display_name = str(signer.get("display_name") or "").strip() or "colegado"
            html_body = self.build_html(
                display_name=display_name,
                minute_number=minute_number,
                title=title,
                sign_url=sign_url,
                template_key=template_key,
                invite_id=invite_id or None,
            )
            try:
                self.mail.send_mail_to(
                    subject=subject,
                    html_body=html_body,
                    to_addresses=[email],
                )
                results.append(
                    self._result(
                        signer=signer,
                        template_key=template_key,
                        mail_send_status=MAIL_SEND_ACCEPTED,
                        mail_delivery_status=MAIL_DELIVERY_TRACE_PENDING,
                        mail_recipient=email,
                    )
                )
            except GraphMailError as exc:
                logger.warning(
                    "tm_mail_send_failed email=%s error=%s",
                    email,
                    str(exc)[:200],
                )
                results.append(
                    self._result(
                        signer=signer,
                        template_key=template_key,
                        mail_send_status=MAIL_SEND_FAILED,
                        mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                        mail_recipient=email,
                        mail_last_error=str(exc)[:480] or None,
                    )
                )
            except Exception as exc:
                logger.exception("tm_mail_send_unexpected email=%s", email)
                results.append(
                    self._result(
                        signer=signer,
                        template_key=template_key,
                        mail_send_status=MAIL_SEND_FAILED,
                        mail_delivery_status=MAIL_DELIVERY_NOT_APPLICABLE,
                        mail_recipient=email,
                        mail_last_error=str(exc)[:480] or None,
                    )
                )
        return results
