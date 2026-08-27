from __future__ import annotations

import io
import secrets
import zipfile
from datetime import date
from typing import Any

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.application.services.content_hash_service import ContentHashService
from cipa_app.application.services.html_sanitizer import CipaHtmlSanitizer
from cipa_app.application.services.cipa_meeting_minute_sign_invite_service import (
    CipaMeetingMinuteSignInviteService,
)
from cipa_app.application.services.portal_notification_service import (
    CipaPortalNotificationService,
)
from cipa_app.application.services.sign_pending_mail_service import (
    CipaSignPendingMailService,
)
from cipa_app.application.services.storage_services import (
    AttachmentStorageService,
    PdfStorageService,
    SignatureStorageService,
)
from cipa_app.domain.services.minute_status_transition_service import (
    MinuteStatusTransitionError,
    MinuteStatusTransitionService,
)
from cipa_app.infrastructure.pdf.minute_pdf_renderer import MinutePdfRenderer
from cipa_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)

_TERMS = (
    "Declaro que li o conteúdo desta ata e confirmo a autenticidade "
    "da minha assinatura eletrônica manuscrita."
)


class MeetingMinutesService:
    def __init__(self) -> None:
        self.repo = MeetingMinuteRepository()
        self.notifications = CipaPortalNotificationService()
        self.sign_invites = CipaMeetingMinuteSignInviteService(self.repo)
        self.sign_pending_mail = CipaSignPendingMailService()
        self.signature_storage = SignatureStorageService()
        self.attachment_storage = AttachmentStorageService()
        self.pdf_storage = PdfStorageService()
        self.pdf_renderer = MinutePdfRenderer()

    def _user_id(self, user) -> str:
        return str(getattr(user, "id", None) or getattr(user, "sub", None) or "")

    @staticmethod
    def _public_actor_id(signer: dict[str, Any], minute: dict[str, Any]) -> str:
        return str(
            signer.get("user_id")
            or minute.get("created_by_user_id")
            or "00000000-0000-0000-0000-000000000001"
        )

    def _assert(self, user, action: str, unit_code: str) -> None:
        perms.assert_unit_action(user, action, unit_code)

    def _load_authorized(self, user, action: str, minute_id: str) -> dict[str, Any]:
        minute = self.repo.get_minute(minute_id)
        if not minute:
            raise LookupError("Ata não encontrada.")
        self._assert(user, action, minute["unit_code"])
        return minute

    def list_minutes(self, user, filters: dict[str, Any]) -> dict[str, Any]:
        units = perms.unit_codes_for_read(user)
        if filters.get("unit_code"):
            code = perms.normalize_unit_code(filters["unit_code"])
            if not code or code not in units:
                raise PermissionError("Sem permissão para a unidade informada.")
            units = [code]
        if not units:
            return {"items": [], "total": 0}
        rows, total = self.repo.list_minutes(
            unit_codes=units,
            status=filters.get("status"),
            meeting_type=filters.get("meeting_type"),
            q=filters.get("q"),
            pending_for_user_id=filters.get("pending_for_me") and self._user_id(user) or None,
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            limit=int(filters.get("limit") or 50),
            offset=int(filters.get("offset") or 0),
        )
        return {"items": rows, "total": total}

    def get_detail(self, user, minute_id: str) -> dict[str, Any]:
        minute = self.repo.get_minute(minute_id)
        if not minute:
            raise LookupError("Ata não encontrada.")
        if not perms.has_unit_read_access(user, minute["unit_code"]):
            raise PermissionError("Sem permissão para visualizar esta ata.")
        version = self.repo.get_version(minute_id)
        signers = self.repo.list_signers(minute_id)
        return {
            "minute": minute,
            "version": version,
            "participants": self.repo.list_participants(minute_id),
            "signers": signers,
            "signatures": self.repo.list_signatures(minute_id),
            "action_items": self.repo.list_action_items(minute_id),
            "versions": self.repo.list_versions(minute_id),
            "viewer": self._build_viewer_context(user, minute, signers),
        }

    def _build_viewer_context(
        self,
        user,
        minute: dict[str, Any],
        signers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Relação do usuário autenticado com a ata — o MFE apenas renderiza."""
        user_id = self._user_id(user)
        signer = next(
            (item for item in signers if str(item.get("user_id") or "") == user_id),
            None,
        )
        signer_status = str(signer.get("status") or "") if signer else ""
        minute_signable = minute.get("status") in {"awaiting_signatures", "partially_signed"}
        return {
            "user_id": user_id or None,
            "is_signer": signer is not None,
            "has_signed": signer_status == "signed",
            "can_sign_now": bool(
                signer and minute_signable and signer_status in {"pending", "viewed"}
            ),
        }

    def create(self, user, payload: dict[str, Any]) -> dict[str, Any]:
        unit_code = perms.normalize_unit_code(payload.get("unit_code"))
        if not unit_code:
            raise ValueError("Unidade inválida.")
        self._assert(user, "create", unit_code)
        agenda = CipaHtmlSanitizer.sanitize(payload.get("agenda_html"))
        body = CipaHtmlSanitizer.sanitize(payload.get("body_html"))
        decisions = CipaHtmlSanitizer.sanitize(payload.get("decisions_html"))
        pending = CipaHtmlSanitizer.sanitize(payload.get("pending_html"))
        observations = CipaHtmlSanitizer.sanitize(payload.get("observations_html"))
        hash_payload = ContentHashService.build_version_payload(
            title=payload["title"],
            meeting_type=payload.get("meeting_type") or "ordinary",
            meeting_date=str(payload["meeting_date"]),
            start_time=str(payload["start_time"]) if payload.get("start_time") else None,
            end_time=str(payload["end_time"]) if payload.get("end_time") else None,
            location=payload.get("location"),
            agenda_html=agenda,
            body_html=body,
            decisions_html=decisions,
            pending_html=pending,
            observations_html=observations,
        )
        content_hash = ContentHashService.hash_version_payload(hash_payload)
        minute = self.repo.create_minute(
            unit_code=unit_code,
            title=payload["title"].strip(),
            meeting_type=payload.get("meeting_type") or "ordinary",
            meeting_date=str(payload["meeting_date"]),
            start_time=payload.get("start_time"),
            end_time=payload.get("end_time"),
            location=payload.get("location"),
            responsible_user_id=payload.get("responsible_user_id") or self._user_id(user),
            responsible_name=payload.get("responsible_name"),
            president_name=payload.get("president_name"),
            secretary_name=payload.get("secretary_name"),
            agenda_html=agenda,
            body_html=body,
            decisions_html=decisions,
            pending_html=pending,
            observations_html=observations,
            content_hash=content_hash,
            created_by_user_id=self._user_id(user),
        )
        participants = payload.get("participants") or []
        if participants:
            self.repo.replace_participants(
                str(minute["id"]),
                unit_code,
                participants,
                self._user_id(user),
            )
        return self.get_detail(user, str(minute["id"]))

    def update(self, user, minute_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        minute = self._load_authorized(user, "edit", minute_id)
        if not MinuteStatusTransitionService.can_edit_content(minute["status"]):
            if MinuteStatusTransitionService.requires_new_version_for_content_change(minute["status"]):
                raise ValueError(
                    "Conteúdo bloqueado após envio para assinatura. Crie uma nova versão."
                )
            raise ValueError("Ata não pode ser editada no status atual.")

        header_fields = {
            key: payload[key]
            for key in (
                "title",
                "meeting_type",
                "meeting_date",
                "start_time",
                "end_time",
                "location",
                "responsible_user_id",
                "responsible_name",
                "president_name",
                "secretary_name",
            )
            if key in payload
        }
        if header_fields:
            minute = self.repo.update_minute_draft(minute_id, header_fields, self._user_id(user))

        content_keys = (
            "agenda_html",
            "body_html",
            "decisions_html",
            "pending_html",
            "observations_html",
        )
        if any(key in payload for key in content_keys):
            current = self.repo.get_version(minute_id)
            if not current:
                raise LookupError("Versão atual não encontrada.")
            agenda = CipaHtmlSanitizer.sanitize(
                payload.get("agenda_html", current.get("agenda_html"))
            )
            body = CipaHtmlSanitizer.sanitize(payload.get("body_html", current.get("body_html")))
            decisions = CipaHtmlSanitizer.sanitize(
                payload.get("decisions_html", current.get("decisions_html"))
            )
            pending = CipaHtmlSanitizer.sanitize(
                payload.get("pending_html", current.get("pending_html"))
            )
            observations = CipaHtmlSanitizer.sanitize(
                payload.get("observations_html", current.get("observations_html"))
            )
            hash_payload = ContentHashService.build_version_payload(
                title=minute["title"],
                meeting_type=minute["meeting_type"],
                meeting_date=str(minute["meeting_date"]),
                start_time=str(minute["start_time"]) if minute.get("start_time") else None,
                end_time=str(minute["end_time"]) if minute.get("end_time") else None,
                location=minute.get("location"),
                agenda_html=agenda,
                body_html=body,
                decisions_html=decisions,
                pending_html=pending,
                observations_html=observations,
            )
            self.repo.update_current_version_content(
                minute_id=minute_id,
                agenda_html=agenda,
                body_html=body,
                decisions_html=decisions,
                pending_html=pending,
                observations_html=observations,
                content_hash=ContentHashService.hash_version_payload(hash_payload),
                actor_user_id=self._user_id(user),
            )

        if "participants" in payload:
            self.repo.replace_participants(
                minute_id,
                minute["unit_code"],
                payload["participants"] or [],
                self._user_id(user),
            )
        if "action_items" in payload:
            self.repo.replace_action_items(
                minute_id, minute["unit_code"], payload["action_items"] or []
            )
        return self.get_detail(user, minute_id)

    def create_version(self, user, minute_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        minute = self._load_authorized(user, "edit", minute_id)
        if MinuteStatusTransitionService.is_terminal(minute["status"]):
            raise ValueError("Ata finalizada/cancelada não aceita nova versão.")
        reason = (payload.get("change_reason") or "").strip()
        if not reason:
            raise ValueError("Informe o motivo da alteração.")
        current = self.repo.get_version(minute_id)
        if not current:
            raise LookupError("Versão atual não encontrada.")

        def _content(field: str) -> str:
            # None = campo não informado — preservar a versão atual (rota envia todas as chaves).
            value = payload.get(field)
            if value is None:
                value = current.get(field)
            return CipaHtmlSanitizer.sanitize(value)

        agenda = _content("agenda_html")
        body = _content("body_html")
        decisions = _content("decisions_html")
        pending = _content("pending_html")
        observations = _content("observations_html")
        hash_payload = ContentHashService.build_version_payload(
            title=minute["title"],
            meeting_type=minute["meeting_type"],
            meeting_date=str(minute["meeting_date"]),
            start_time=str(minute["start_time"]) if minute.get("start_time") else None,
            end_time=str(minute["end_time"]) if minute.get("end_time") else None,
            location=minute.get("location"),
            agenda_html=agenda,
            body_html=body,
            decisions_html=decisions,
            pending_html=pending,
            observations_html=observations,
        )
        result = self.repo.create_new_version(
            minute_id=minute_id,
            change_reason=reason,
            agenda_html=agenda,
            body_html=body,
            decisions_html=decisions,
            pending_html=pending,
            observations_html=observations,
            content_hash=ContentHashService.hash_version_payload(hash_payload),
            actor_user_id=self._user_id(user),
        )
        return {"minute": result["minute"], "version": result["version"]}

    def set_signers(self, user, minute_id: str, signers: list[dict[str, Any]]) -> dict[str, Any]:
        minute = self._load_authorized(user, "manage_signers", minute_id)
        if not MinuteStatusTransitionService.can_edit_content(minute["status"]):
            raise ValueError("Signatários só podem ser alterados em rascunho/revisão.")
        if not minute.get("current_version_id"):
            raise ValueError("Ata sem versão corrente.")
        cleaned = []
        for item in signers:
            if not item.get("user_id") or not item.get("display_name"):
                raise ValueError("Cada signatário precisa de user_id e display_name.")
            cleaned.append(item)
        rows = self.repo.replace_signers(
            minute_id=minute_id,
            version_id=str(minute["current_version_id"]),
            unit_code=minute["unit_code"],
            signers=cleaned,
            actor_user_id=self._user_id(user),
        )
        return {"signers": rows}

    def transition(self, user, minute_id: str, to_status: str, reason: str | None = None) -> dict[str, Any]:
        action_by_status = {
            "in_review": "submit",
            "draft": "edit",
            "awaiting_signatures": "submit",
            "cancelled": "cancel",
            "finalized": "finalize",
        }
        action = action_by_status.get(to_status)
        if not action:
            raise ValueError("Status de destino não suportado por transition.")
        minute = self._load_authorized(user, action, minute_id)
        try:
            MinuteStatusTransitionService.assert_transition(minute["status"], to_status)
        except MinuteStatusTransitionError as exc:
            raise ValueError(str(exc)) from exc
        if to_status == "cancelled" and not (reason or "").strip():
            raise ValueError("Cancelamento exige justificativa.")
        if to_status == "awaiting_signatures":
            return self.send_for_signature(user, minute_id)
        if to_status == "finalized":
            return self.finalize(user, minute_id)
        updated = self.repo.set_status(
            minute_id=minute_id,
            status=to_status,
            actor_user_id=self._user_id(user),
            action=f"transition_{to_status}",
            extra={"cancel_reason": reason} if to_status == "cancelled" else None,
        )
        return {"minute": updated}

    def send_for_signature(self, user, minute_id: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "submit", minute_id)
        try:
            MinuteStatusTransitionService.assert_transition(minute["status"], "awaiting_signatures")
        except MinuteStatusTransitionError as exc:
            raise ValueError(str(exc)) from exc
        signers = self.repo.list_signers(minute_id)
        if not signers:
            raise ValueError("Configure ao menos um signatário antes de enviar.")
        updated = self.repo.set_status(
            minute_id=minute_id,
            status="awaiting_signatures",
            actor_user_id=self._user_id(user),
            action="send_for_signature",
        )
        self._dispatch_sign_invites(updated, signers, template_key="signPending")
        return {"minute": updated, "signers": signers}

    def resend_sign_invites(self, user, minute_id: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "submit", minute_id)
        if minute.get("status") not in {"awaiting_signatures", "partially_signed"}:
            raise ValueError(
                "Reenvio só é permitido enquanto a ata aguarda assinaturas. "
                "Se a ata estiver em revisão, use «Enviar para assinatura»."
            )
        signers = self.repo.list_signers(minute_id)
        targets = [
            signer
            for signer in signers
            if str(signer.get("status") or "") in {"pending", "viewed"}
        ]
        if not targets:
            raise ValueError("Não há signatários pendentes para reenviar.")
        dispatched = self._dispatch_sign_invites(
            minute,
            targets,
            template_key="signPendingReminder",
        )
        return {
            "minute": minute,
            "signers": targets,
            "resent_count": dispatched["resent_count"],
            "mail_sent": dispatched["mail_sent"],
        }

    def _dispatch_sign_invites(
        self,
        minute: dict[str, Any],
        signers: list[dict[str, Any]],
        *,
        template_key: str = "signPending",
    ) -> dict[str, Any]:
        mail_signers: list[dict[str, Any]] = []
        minute_id = str(minute["id"])
        minute_number = str(minute.get("minute_number") or "")
        minute_title = str(minute.get("title") or "")
        unit_code = str(minute.get("unit_code") or "")

        for signer in signers:
            issued = self.sign_invites.issue(signer=signer, minute=minute)
            invite = issued.get("invite") or {}
            invite_id = str(invite.get("id") or "").strip()
            mail_signers.append({**signer, "sign_url": issued["sign_url"]})
            user_id = str(signer.get("user_id") or "").strip()
            if user_id:
                dedupe = (
                    f"cipa:sign_pending:{minute_id}:{user_id}:{invite_id}"
                    if invite_id
                    else None
                )
                self.notifications.notify_sign_pending(
                    user_id=user_id,
                    minute_id=minute_id,
                    minute_number=minute_number,
                    title=minute_title,
                    unit_code=unit_code,
                    dedupe_key=dedupe,
                )
        mail_sent = self.sign_pending_mail.notify_signers(
            signers=mail_signers,
            minute_number=minute_number,
            title=minute_title,
            template_key=template_key,
        )
        return {"resent_count": len(mail_signers), "mail_sent": mail_sent}

    def sign_context(self, user, minute_id: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "sign", minute_id)
        signer = self.repo.get_signer_for_user(minute_id, self._user_id(user))
        if not signer:
            raise PermissionError("Você não é signatário desta ata.")
        if signer["status"] in {"pending", "viewed"}:
            self.repo.mark_signer_viewed(str(signer["id"]))
            signer = self.repo.get_signer_for_user(minute_id, self._user_id(user))
        version = self.repo.get_version(minute_id)
        return {
            "minute": minute,
            "version": version,
            "signer": signer,
            "participants": self.repo.list_participants(minute_id),
            "signers": self.repo.list_signers(minute_id),
            "signatures": self.repo.list_signatures(minute_id),
            "terms": _TERMS,
        }

    def public_sign_context(self, raw_token: str) -> dict[str, Any]:
        resolved = self.sign_invites.resolve(raw_token)
        minute = resolved["minute"]
        signer = resolved["signer"]
        outcome = str(resolved.get("outcome") or "ready")
        if outcome != "already_signed" and signer.get("status") in {"pending", "viewed"}:
            self.repo.mark_signer_viewed(str(signer["id"]))
            signer = self.repo.get_signer(str(signer["id"])) or signer
        version_id = (
            str(signer.get("version_id") or "").strip() or None
            if outcome == "already_signed"
            else None
        )
        version = self.repo.get_version(str(minute["id"]), version_id=version_id)
        if outcome == "already_signed" and not version:
            version = self.repo.get_version(str(minute["id"]))
        minute_id = str(minute["id"])
        preview_version_id = str(version.get("id") or "").strip() or None if version else None
        return {
            "outcome": outcome,
            "minute": {
                "id": minute["id"],
                "title": minute.get("title"),
                "minute_number": minute.get("minute_number"),
                "meeting_date": minute.get("meeting_date"),
                "meeting_type": minute.get("meeting_type"),
                "location": minute.get("location"),
                "start_time": minute.get("start_time"),
                "end_time": minute.get("end_time"),
                "status": minute.get("status"),
                "unit_code": minute.get("unit_code"),
            },
            "version": {
                "id": version.get("id") if version else None,
                "title": version.get("title") if version else None,
                "agenda_html": version.get("agenda_html") if version else "",
                "body_html": version.get("body_html") if version else "",
                "decisions_html": version.get("decisions_html") if version else "",
                "pending_html": version.get("pending_html") if version else "",
                "observations_html": version.get("observations_html") if version else "",
                "content_hash": version.get("content_hash") if version else None,
            },
            "signer": {
                "id": signer["id"],
                "display_name": signer.get("display_name"),
                "status": signer.get("status"),
            },
            "participants": self.repo.list_participants(minute_id),
            "signers": self.repo.list_signers(minute_id),
            "signatures": [
                {
                    "id": item.get("id"),
                    "signer_id": item.get("signer_id"),
                    "user_id": item.get("user_id"),
                    "display_name_confirmed": item.get("display_name_confirmed"),
                    "has_image": bool(str(item.get("image_path") or "").strip()),
                }
                for item in self.repo.list_signatures(minute_id, version_id=preview_version_id)
            ],
            "terms": _TERMS,
        }

    def public_signature_image(self, raw_token: str, signature_id: str) -> bytes:
        resolved = self.sign_invites.resolve(raw_token)
        minute = resolved["minute"]
        signature = self.repo.get_signature_for_minute(str(minute["id"]), signature_id)
        if not signature or not signature.get("image_path"):
            raise LookupError("Imagem de assinatura não encontrada.")
        return self.signature_storage.read(str(signature["image_path"]))

    def signature_image(self, user, minute_id: str, signature_id: str) -> bytes:
        minute = self.repo.get_minute(minute_id)
        if not minute:
            raise LookupError("Ata não encontrada.")
        if not perms.has_unit_read_access(user, minute["unit_code"]):
            raise PermissionError("Sem permissão para visualizar esta ata.")
        signature = self.repo.get_signature(minute_id, signature_id)
        if not signature or not signature.get("image_path"):
            raise LookupError("Imagem de assinatura não encontrada.")
        return self.signature_storage.read(str(signature["image_path"]))

    def sign(
        self,
        user,
        minute_id: str,
        *,
        png_bytes: bytes,
        display_name_confirmed: str,
        terms_accepted: bool,
        client_ip: str | None,
        user_agent: str | None,
        session_id: str | None,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        minute = self._load_authorized(user, "sign", minute_id)
        if minute["status"] not in {"awaiting_signatures", "partially_signed"}:
            raise ValueError("Ata não está aguardando assinaturas.")
        if not terms_accepted:
            raise ValueError("É necessário aceitar o termo de ciência.")
        if not (display_name_confirmed or "").strip():
            raise ValueError("Confirme o nome do signatário.")
        signer = self.repo.get_signer_for_user(minute_id, self._user_id(user))
        if not signer:
            raise PermissionError("Você não é signatário desta ata.")
        if str(signer["user_id"]) != self._user_id(user):
            raise PermissionError("Não é permitido assinar em nome de outro usuário.")
        version = self.repo.get_version(minute_id)
        if not version:
            raise LookupError("Versão não encontrada.")
        image_path = self.signature_storage.save_png(
            unit_code=minute["unit_code"],
            minute_id=minute_id,
            raw=png_bytes,
        )
        result = self.repo.register_signature(
            minute_id=minute_id,
            version_id=str(version["id"]),
            signer_id=str(signer["id"]),
            unit_code=minute["unit_code"],
            user_id=self._user_id(user),
            display_name_confirmed=display_name_confirmed.strip(),
            content_hash=version["content_hash"],
            image_path=image_path,
            terms_accepted=terms_accepted,
            client_ip=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            idempotency_key=idempotency_key,
            actor_user_id=self._user_id(user),
        )
        if result.get("duplicate"):
            return {"signature": result["signature"], "minute": minute, "duplicate": True}
        self.repo.invalidate_open_invites(signer_id=str(signer["id"]))
        new_status = MinuteStatusTransitionService.status_after_signature_progress(
            signed_count=result["signed_count"],
            required_count=result["required_count"],
        )
        if new_status != minute["status"]:
            minute = self.repo.set_status(
                minute_id=minute_id,
                status=new_status,
                actor_user_id=self._user_id(user),
                action="signature_progress",
            )
            if new_status == "signed" and minute.get("responsible_user_id"):
                self.notifications.notify_minute_signed(
                    user_id=str(minute["responsible_user_id"]),
                    minute_id=str(minute["id"]),
                    minute_number=str(minute.get("minute_number") or ""),
                    title=str(minute.get("title") or ""),
                    unit_code=str(minute.get("unit_code") or ""),
                )
        return {"signature": result["signature"], "minute": minute, "duplicate": False}

    def public_sign(
        self,
        raw_token: str,
        *,
        png_bytes: bytes,
        display_name_confirmed: str,
        terms_accepted: bool,
        client_ip: str | None,
        user_agent: str | None,
        session_id: str | None,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        resolved = self.sign_invites.resolve(raw_token)
        if resolved.get("outcome") == "already_signed":
            raise ValueError("Esta assinatura já foi registrada.")
        minute = resolved["minute"]
        signer = resolved["signer"]
        invite = resolved["invite"]
        if not terms_accepted or not (display_name_confirmed or "").strip():
            raise ValueError("É necessário aceitar o termo e confirmar o nome do signatário.")
        version = self.repo.get_version(str(minute["id"]))
        if not version:
            raise LookupError("Versão não encontrada.")
        actor_id = self._public_actor_id(signer, minute)
        user_id = str(signer.get("user_id") or "").strip()
        if not user_id:
            raise ValueError("Signatário sem usuário vinculado.")
        image_path = self.signature_storage.save_png(
            unit_code=minute["unit_code"],
            minute_id=str(minute["id"]),
            raw=png_bytes,
        )
        result = self.repo.register_signature(
            minute_id=str(minute["id"]),
            version_id=str(version["id"]),
            signer_id=str(signer["id"]),
            unit_code=str(minute["unit_code"]),
            user_id=user_id,
            display_name_confirmed=display_name_confirmed.strip(),
            content_hash=version["content_hash"],
            image_path=image_path,
            terms_accepted=True,
            client_ip=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            idempotency_key=idempotency_key,
            actor_user_id=actor_id,
        )
        self.sign_invites.consume(str(invite["id"]))
        if result.get("duplicate"):
            return {"signature": result["signature"], "minute": minute, "duplicate": True}
        new_status = MinuteStatusTransitionService.status_after_signature_progress(
            signed_count=result["signed_count"],
            required_count=result["required_count"],
        )
        if new_status != minute["status"]:
            minute = self.repo.set_status(
                minute_id=str(minute["id"]),
                status=new_status,
                actor_user_id=actor_id,
                action="signature_progress",
            )
            if new_status == "signed" and minute.get("responsible_user_id"):
                self.notifications.notify_minute_signed(
                    user_id=str(minute["responsible_user_id"]),
                    minute_id=str(minute["id"]),
                    minute_number=str(minute.get("minute_number") or ""),
                    title=str(minute.get("title") or ""),
                    unit_code=str(minute.get("unit_code") or ""),
                )
        return {"signature": result["signature"], "minute": minute, "duplicate": False}

    def refuse(self, user, minute_id: str, reason: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "sign", minute_id)
        if not (reason or "").strip():
            raise ValueError("Informe a justificativa da recusa.")
        signer = self.repo.get_signer_for_user(minute_id, self._user_id(user))
        if not signer:
            raise PermissionError("Você não é signatário desta ata.")
        self.repo.refuse_signature(
            minute_id=minute_id,
            signer_id=str(signer["id"]),
            reason=reason.strip(),
            actor_user_id=self._user_id(user),
            unit_code=minute["unit_code"],
        )
        self.repo.invalidate_open_invites(signer_id=str(signer["id"]))
        updated = self.repo.set_status(
            minute_id=minute_id,
            status="in_review",
            actor_user_id=self._user_id(user),
            action="signature_refused",
        )
        if updated.get("responsible_user_id"):
            self.notifications.notify_minute_refused(
                user_id=str(updated["responsible_user_id"]),
                minute_id=str(updated["id"]),
                minute_number=str(updated.get("minute_number") or ""),
                title=str(updated.get("title") or ""),
                unit_code=str(updated.get("unit_code") or ""),
                actor_name=str(signer.get("display_name") or "Signatário"),
                reason=reason.strip(),
            )
        return {"minute": updated}

    def public_refuse(self, raw_token: str, reason: str) -> dict[str, Any]:
        if not (reason or "").strip():
            raise ValueError("Informe a justificativa da recusa.")
        resolved = self.sign_invites.resolve(raw_token)
        if resolved.get("outcome") == "already_signed":
            raise ValueError("Esta assinatura já foi registrada.")
        minute = resolved["minute"]
        signer = resolved["signer"]
        invite = resolved["invite"]
        actor_id = self._public_actor_id(signer, minute)
        self.repo.refuse_signature(
            minute_id=str(minute["id"]),
            signer_id=str(signer["id"]),
            reason=reason.strip(),
            actor_user_id=actor_id,
            unit_code=str(minute["unit_code"]),
        )
        self.sign_invites.consume(str(invite["id"]))
        updated = self.repo.set_status(
            minute_id=str(minute["id"]),
            status="in_review",
            actor_user_id=actor_id,
            action="signature_refused",
        )
        if updated.get("responsible_user_id"):
            self.notifications.notify_minute_refused(
                user_id=str(updated["responsible_user_id"]),
                minute_id=str(updated["id"]),
                minute_number=str(updated.get("minute_number") or ""),
                title=str(updated.get("title") or ""),
                unit_code=str(updated.get("unit_code") or ""),
                actor_name=str(signer.get("display_name") or "Signatário"),
                reason=reason.strip(),
            )
        return {"minute": updated}

    def finalize(self, user, minute_id: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "finalize", minute_id)
        try:
            MinuteStatusTransitionService.assert_transition(minute["status"], "finalized")
        except MinuteStatusTransitionError as exc:
            raise ValueError(str(exc)) from exc
        version = self.repo.get_version(minute_id)
        if not version:
            raise LookupError("Versão não encontrada.")
        validation_code = secrets.token_urlsafe(12)
        minute_for_pdf = {
            **minute,
            "validation_code": validation_code,
            "final_content_hash": version["content_hash"],
        }
        pdf_bytes = self._render_pdf(minute_for_pdf, version)
        pdf_path = self.pdf_storage.save(
            unit_code=minute["unit_code"], minute_id=minute_id, raw=pdf_bytes
        )
        updated = self.repo.set_status(
            minute_id=minute_id,
            status="finalized",
            actor_user_id=self._user_id(user),
            action="finalize",
            extra={
                "final_pdf_path": pdf_path,
                "final_content_hash": version["content_hash"],
                "validation_code": validation_code,
            },
        )
        return {"minute": updated}

    def export_pdf(self, user, minute_id: str) -> tuple[bytes, str]:
        minute = self._load_authorized(user, "export", minute_id)
        if minute.get("final_pdf_path"):
            raw = self.pdf_storage.read(minute["final_pdf_path"])
            return raw, f"ata-cipa-{minute['minute_number'].replace('/', '-')}.pdf"
        version = self.repo.get_version(minute_id)
        if not version:
            raise LookupError("Versão não encontrada.")
        raw = self._render_pdf(minute, version)
        return raw, f"ata-cipa-{minute['minute_number'].replace('/', '-')}.pdf"

    def export_filtered_pdfs(self, user, filters: dict[str, Any]) -> tuple[bytes, str]:
        """ZIP com um PDF oficial por ata que casa com os filtros da listagem."""
        unit_code = perms.normalize_unit_code(filters.get("unit_code"))
        if not unit_code:
            raise ValueError("Informe a unidade para exportar as atas filtradas.")
        self._assert(user, "export", unit_code)

        listed = self.list_minutes(
            user,
            {
                "unit_code": unit_code,
                "status": filters.get("status"),
                "meeting_type": filters.get("meeting_type"),
                "q": filters.get("q"),
                "date_from": filters.get("date_from"),
                "date_to": filters.get("date_to"),
                "limit": int(filters.get("limit") or 200),
                "offset": int(filters.get("offset") or 0),
            },
        )
        items = listed.get("items") or []
        if not items:
            raise LookupError("Nenhuma ata encontrada para os filtros atuais.")

        buffer = io.BytesIO()
        used_names: set[str] = set()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in items:
                minute_id = str(item.get("id") or "")
                if not minute_id:
                    continue
                raw, filename = self.export_pdf(user, minute_id)
                archive.writestr(self._unique_zip_name(filename, used_names), raw)

        stamp = date.today().isoformat()
        return buffer.getvalue(), f"atas-cipa-{unit_code}-{stamp}.zip"

    @staticmethod
    def _unique_zip_name(filename: str, used_names: set[str]) -> str:
        if filename not in used_names:
            used_names.add(filename)
            return filename
        stem, _, suffix = filename.rpartition(".")
        index = 2
        while True:
            candidate = f"{stem}-{index}.{suffix}" if suffix else f"{filename}-{index}"
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            index += 1

    def _render_pdf(
        self,
        minute: dict[str, Any],
        version: dict[str, Any],
    ) -> bytes:
        participants = self.repo.list_participants(str(minute["id"]))
        signers = self.repo.list_signers(str(minute["id"]))
        signatures = []
        for signature in self.repo.list_signatures(str(minute["id"])):
            enriched = dict(signature)
            image_path = signature.get("image_path")
            if image_path:
                enriched["image_bytes"] = self.signature_storage.read(str(image_path))
            signatures.append(enriched)
        return self.pdf_renderer.render(
            minute,
            version,
            participants,
            signers,
            signatures,
        )

    def audit(self, user, minute_id: str) -> dict[str, Any]:
        minute = self.repo.get_minute(minute_id)
        if not minute:
            raise LookupError("Ata não encontrada.")
        if not perms.has_unit_read_access(user, minute["unit_code"]):
            raise PermissionError("Sem permissão para consultar auditoria desta ata.")
        return {"items": self.repo.list_audit(minute_id)}

    def soft_delete(self, user, minute_id: str) -> dict[str, Any]:
        minute = self._load_authorized(user, "delete", minute_id)
        if not MinuteStatusTransitionService.can_delete(minute["status"]):
            raise ValueError("Atas assinadas ou finalizadas não podem ser excluídas.")
        return {"minute": self.repo.soft_delete(minute_id, self._user_id(user))}

    def add_attachment(
        self,
        user,
        minute_id: str,
        *,
        file_name: str,
        content_type: str,
        raw: bytes,
    ) -> dict[str, Any]:
        minute = self._load_authorized(user, "edit", minute_id)
        if not MinuteStatusTransitionService.can_edit_content(minute["status"]):
            raise ValueError("Anexos só podem ser adicionados em rascunho/revisão.")
        path = self.attachment_storage.save(
            unit_code=minute["unit_code"],
            minute_id=minute_id,
            file_name=file_name,
            content_type=content_type,
            raw=raw,
        )
        row = self.repo.add_attachment(
            minute_id=minute_id,
            unit_code=minute["unit_code"],
            file_name=file_name,
            content_type=content_type,
            size_bytes=len(raw),
            storage_path=path,
            uploaded_by_user_id=self._user_id(user),
        )
        return {"attachment": row}

    def pending_signatures(self, user) -> dict[str, Any]:
        units = perms.unit_codes_for_action(user, "sign")
        if not units:
            return {"items": [], "total": 0}
        rows, total = self.repo.list_minutes(
            unit_codes=units,
            pending_for_user_id=self._user_id(user),
            limit=100,
            offset=0,
        )
        return {"items": rows, "total": total}
