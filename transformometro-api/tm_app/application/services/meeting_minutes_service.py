from __future__ import annotations

import secrets
from typing import Any

from tm_app.application.security import transformometro_permissions as perms
from tm_app.application.services.content_hash_service import ContentHashService
from tm_app.application.services.html_sanitizer import TmAtaHtmlSanitizer
from tm_app.application.services.meeting_minutes_storage import PdfStorageService, SignatureStorageService
from tm_app.application.services.tm_portal_notification_service import TmPortalNotificationService
from tm_app.application.services.tm_meeting_minute_sign_invite_service import (
    TmMeetingMinuteSignInviteService,
)
from tm_app.application.services.tm_sign_pending_mail_service import TmSignPendingMailService
from tm_app.application.services.filial_access_scope_service import FilialAccessScopeService
from tm_app.domain.services.minute_status_transition_service import MinuteStatusTransitionError, MinuteStatusTransitionService
from tm_app.infrastructure.pdf.minute_pdf_renderer import MinutePdfRenderer
from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import MeetingMinuteRepository

_TERMS = (
    "Declaro que li o conteúdo desta ata e confirmo a autenticidade "
    "da minha assinatura eletrônica manuscrita."
)


class MeetingMinutesService:
    def __init__(
        self,
        repo: MeetingMinuteRepository | None = None,
        *,
        notifications: TmPortalNotificationService | None = None,
        sign_invites: TmMeetingMinuteSignInviteService | None = None,
        sign_pending_mail: TmSignPendingMailService | None = None,
    ) -> None:
        self.repo = repo or MeetingMinuteRepository()
        self.notifications = notifications or TmPortalNotificationService()
        self.sign_invites = sign_invites or TmMeetingMinuteSignInviteService(self.repo)
        self.sign_pending_mail = sign_pending_mail or TmSignPendingMailService()
        self.signature_storage, self.pdf_storage = SignatureStorageService(), PdfStorageService()
        self.pdf_renderer, self.scope_service = MinutePdfRenderer(), FilialAccessScopeService()

    @staticmethod
    def _user_id(user: Any) -> str:
        return str(getattr(user, "id", None) or getattr(user, "sub", None) or "")

    @staticmethod
    def _public_actor_id(signer: dict[str, Any], minute: dict[str, Any]) -> str:
        return str(
            signer.get("user_id")
            or minute.get("created_by_user_id")
            or "00000000-0000-0000-0000-000000000001"
        )

    def _permissions(self, user: Any) -> set[str]:
        return set(getattr(user, "permissions", []) or [])

    def _has_any_permission(self, user: Any, *codes: str) -> bool:
        if getattr(user, "is_superadmin", False):
            return True
        permissions = self._permissions(user)
        return any(code in permissions for code in codes)

    def _assert(self, user: Any, action: str, unit_code: str) -> None:
        permissions = self._permissions(user)
        if getattr(user, "is_superadmin", False):
            return
        if action == "view":
            # Leitura: view, manage ou sign (sign-only precisa de detalhe/imagem no fluxo de assinar).
            if not any(code in permissions for code in perms.MEETING_MINUTES_READ_PERMISSIONS):
                raise PermissionError("Sem permissão para esta operação de atas.")
        else:
            required = {
                "manage": perms.MEETING_MINUTES_MANAGE_PERMISSIONS,
                "sign": perms.MEETING_MINUTES_SIGN_PERMISSIONS,
            }[action]
            if not any(code in permissions for code in required):
                raise PermissionError("Sem permissão para esta operação de atas.")
        scope = self.scope_service.resolve(user)
        if action == "view":
            allowed = self.scope_service.can_view_filial(scope, unit_code)
        else:
            allowed = self.scope_service.can_manage_filial(scope, unit_code, user=user) if action == "manage" else self.scope_service.can_view_filial(scope, unit_code)
        if not allowed:
            raise PermissionError("Sem permissão para acessar esta unidade.")

    def _load(self, user: Any, action: str, minute_id: str) -> dict[str, Any]:
        minute = self.repo.get_minute(minute_id)
        if not minute: raise LookupError("Ata não encontrada.")
        self._assert(user, action, str(minute["unit_code"]))
        return minute

    def _hash(self, minute: dict[str, Any], content: dict[str, str]) -> str:
        return ContentHashService.hash_version_payload(ContentHashService.build_version_payload(
            title=minute["title"], meeting_type=minute["meeting_type"], meeting_date=str(minute["meeting_date"]),
            start_time=str(minute["start_time"]) if minute.get("start_time") else None,
            end_time=str(minute["end_time"]) if minute.get("end_time") else None, location=minute.get("location"), **content))

    def list_minutes(self, user: Any, filters: dict[str, Any]) -> dict[str, Any]:
        pending_for_me = bool(filters.get("pending_for_me"))
        if pending_for_me:
            if not self._has_any_permission(user, *perms.MEETING_MINUTES_READ_PERMISSIONS):
                raise PermissionError("Sem permissão para consultar atas.")
        elif not self._has_any_permission(user, *perms.MEETING_MINUTES_LIST_PERMISSIONS):
            raise PermissionError("Sem permissão para consultar atas.")
        scope = self.scope_service.resolve(user)
        units = ["01", "02"] if scope.is_unrestricted else sorted(scope.allowed_codigos)
        if filters.get("unit_code"):
            self._assert(user, "view", str(filters["unit_code"]))
            units = [str(filters["unit_code"]).zfill(2)]
        if not units:
            return {"items": [], "total": 0}
        rows, total = self.repo.list_minutes(
            unit_codes=units,
            status=filters.get("status"),
            meeting_type=filters.get("meeting_type"),
            q=filters.get("q"),
            pending_for_user_id=self._user_id(user) if pending_for_me else None,
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            limit=int(filters.get("limit") or 50),
            offset=int(filters.get("offset") or 0),
        )
        return {"items": rows, "total": total}

    def _sync_signers(self, user: Any, minute_id: str, payload: dict[str, Any]) -> None:
        minute = self.repo.get_minute(minute_id)
        if not minute or not minute.get("current_version_id"):
            return
        signers = payload.get("signers")
        if signers is None:
            signers = []
            for index, item in enumerate(payload.get("participants") or []):
                if not item.get("must_sign") or not item.get("display_name"):
                    continue
                user_id = item.get("user_id")
                invite_email = str(item.get("invite_email") or "").strip() or None
                if not user_id and not invite_email:
                    continue
                signers.append(
                    {
                        "user_id": user_id,
                        "invite_email": invite_email,
                        "display_name": item["display_name"],
                        "sign_order": index + 1,
                    }
                )
        if any(
            not item.get("display_name")
            or (not item.get("user_id") and not str(item.get("invite_email") or "").strip())
            for item in signers
        ):
            raise ValueError("Cada signatário precisa de display_name e user_id ou invite_email.")
        self.repo.replace_signers(
            minute_id=minute_id,
            version_id=str(minute["current_version_id"]),
            unit_code=str(minute["unit_code"]),
            signers=signers,
            actor_user_id=self._user_id(user),
        )

    def get_detail(self, user: Any, minute_id: str) -> dict[str, Any]:
        minute=self._load(user,"view",minute_id); signers=self.repo.list_signers(minute_id); user_id=self._user_id(user)
        signer=next((s for s in signers if str(s.get("user_id"))==user_id),None)
        return {"minute":minute,"version":self.repo.get_version(minute_id),"participants":self.repo.list_participants(minute_id),"signers":signers,"signatures":self.repo.list_signatures(minute_id),"versions":self.repo.list_versions(minute_id),"viewer":{"user_id":user_id or None,"is_signer":bool(signer),"has_signed":bool(signer and signer["status"]=="signed"),"can_sign_now":bool(signer and minute["status"] in {"awaiting_signatures","partially_signed"} and signer["status"] in {"pending","viewed"})}}

    def create(self, user: Any, payload: dict[str, Any]) -> dict[str, Any]:
        unit = str(payload.get("unit_code") or "").zfill(2)
        self._assert(user, "manage", unit)
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Informe o título da ata.")
        if not payload.get("meeting_date"):
            raise ValueError("Informe a data da reunião.")
        content = {
            key: TmAtaHtmlSanitizer.sanitize(payload.get(key))
            for key in ("agenda_html", "body_html", "decisions_html", "pending_html", "observations_html")
        }
        header = {
            **payload,
            "unit_code": unit,
            "meeting_type": payload.get("meeting_type") or "ordinary",
            "title": title,
            "created_by_user_id": self._user_id(user),
            **content,
        }
        header["content_hash"] = self._hash(header, content)
        minute = self.repo.create_minute(**header)
        minute_id = str(minute["id"])
        if payload.get("participants"):
            self.repo.replace_participants(minute_id, unit, payload["participants"], self._user_id(user))
        if "signers" in payload or payload.get("participants"):
            self._sync_signers(user, minute_id, payload)
        return self.get_detail(user, minute_id)

    def update(self, user: Any, minute_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        minute = self._load(user, "manage", minute_id)
        if not MinuteStatusTransitionService.can_edit_content(minute["status"]):
            raise ValueError(
                "Conteúdo bloqueado após envio para assinatura. Crie uma nova versão."
                if MinuteStatusTransitionService.requires_new_version_for_content_change(minute["status"])
                else "Ata não pode ser editada no status atual."
            )
        fields = {
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
                "chair_name",
                "secretary_name",
            )
            if key in payload
        }
        if fields:
            minute = self.repo.update_minute_draft(minute_id, fields, self._user_id(user))
        keys = ("agenda_html", "body_html", "decisions_html", "pending_html", "observations_html")
        if any(key in payload for key in keys):
            current = self.repo.get_version(minute_id)
            if not current:
                raise LookupError("Versão atual não encontrada.")
            content = {
                key: TmAtaHtmlSanitizer.sanitize(payload.get(key, current.get(key))) for key in keys
            }
            self.repo.update_current_version_content(
                minute_id=minute_id,
                actor_user_id=self._user_id(user),
                content_hash=self._hash(minute, content),
                **content,
            )
        if "participants" in payload:
            self.repo.replace_participants(
                minute_id, str(minute["unit_code"]), payload["participants"] or [], self._user_id(user)
            )
        if "signers" in payload or "participants" in payload:
            self._sync_signers(user, minute_id, payload)
        return self.get_detail(user, minute_id)

    def create_version(self,user: Any,minute_id: str,payload: dict[str,Any]) -> dict[str,Any]:
        minute=self._load(user,"manage",minute_id)
        if MinuteStatusTransitionService.is_terminal(minute["status"]): raise ValueError("Ata finalizada/cancelada não aceita nova versão.")
        reason=str(payload.get("change_reason") or "").strip()
        if not reason: raise ValueError("Informe o motivo da alteração.")
        current=self.repo.get_version(minute_id)
        if not current: raise LookupError("Versão atual não encontrada.")
        content={key:TmAtaHtmlSanitizer.sanitize(payload.get(key) if payload.get(key) is not None else current.get(key)) for key in ("agenda_html","body_html","decisions_html","pending_html","observations_html")}
        return self.repo.create_new_version(minute_id=minute_id,change_reason=reason,content_hash=self._hash(minute,content),actor_user_id=self._user_id(user),**content)

    def set_participants(self,user: Any,minute_id: str,participants:list[dict[str,Any]]) -> dict[str,Any]:
        return self.update(user,minute_id,{"participants":participants})
    def set_signers(self,user: Any,minute_id: str,signers:list[dict[str,Any]]) -> dict[str,Any]:
        minute=self._load(user,"manage",minute_id)
        if not MinuteStatusTransitionService.can_edit_content(minute["status"]): raise ValueError("Signatários só podem ser alterados em rascunho/revisão.")
        if any(
            not s.get("display_name")
            or (not s.get("user_id") and not str(s.get("invite_email") or "").strip())
            for s in signers
        ):
            raise ValueError("Cada signatário precisa de display_name e user_id ou invite_email.")
        return {"signers":self.repo.replace_signers(minute_id=minute_id,version_id=str(minute["current_version_id"]),unit_code=str(minute["unit_code"]),signers=signers,actor_user_id=self._user_id(user))}

    def send_for_signature(self,user: Any,minute_id: str) -> dict[str,Any]:
        minute=self._load(user,"manage",minute_id)
        try: MinuteStatusTransitionService.assert_transition(minute["status"],"awaiting_signatures")
        except MinuteStatusTransitionError as exc: raise ValueError(str(exc)) from exc
        signers=self.repo.list_signers(minute_id)
        if not signers: raise ValueError("Configure ao menos um signatário antes de enviar.")
        updated=self.repo.set_status(minute_id=minute_id,status="awaiting_signatures",actor_user_id=self._user_id(user),action="send_for_signature")
        mail_signers: list[dict[str, Any]] = []
        for signer in signers:
            issued = self.sign_invites.issue(signer=signer, minute=updated)
            payload = {
                **signer,
                "sign_url": issued["sign_url"],
                "raw_token": issued["raw_token"],
            }
            mail_signers.append(payload)
            user_id = str(signer.get("user_id") or "").strip()
            if user_id:
                self.notifications.notify_sign_pending(
                    user_id=user_id,
                    minute_id=str(updated["id"]),
                    minute_number=str(updated["minute_number"]),
                    title=str(updated.get("title") or ""),
                )
        self.sign_pending_mail.notify_signers(
            signers=mail_signers,
            minute_number=str(updated["minute_number"]),
            title=str(updated.get("title") or ""),
        )
        return {"minute":updated,"signers":signers}

    def sign_context(self,user: Any,minute_id: str) -> dict[str,Any]:
        minute=self._load(user,"sign",minute_id); signer=self.repo.get_signer_for_user(minute_id,self._user_id(user))
        if not signer: raise PermissionError("Você não é signatário desta ata.")
        if signer["status"] in {"pending","viewed"}: signer=self.repo.mark_signer_viewed(str(signer["id"])) or signer
        return {"minute":minute,"version":self.repo.get_version(minute_id),"signer":signer,"participants":self.repo.list_participants(minute_id),"signers":self.repo.list_signers(minute_id),"signatures":self.repo.list_signatures(minute_id),"terms":_TERMS}

    def public_sign_context(self, raw_token: str) -> dict[str, Any]:
        resolved = self.sign_invites.resolve(raw_token)
        minute = resolved["minute"]
        signer = resolved["signer"]
        if signer["status"] in {"pending", "viewed"}:
            signer = self.repo.mark_signer_viewed(str(signer["id"])) or signer
        version = self.repo.get_version(str(minute["id"]))
        return {
            "minute": {
                "id": minute["id"],
                "title": minute.get("title"),
                "minute_number": minute.get("minute_number"),
                "meeting_date": minute.get("meeting_date"),
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
            "terms": _TERMS,
        }

    def _notify_managers_signed(self, minute: dict[str, Any]) -> None:
        for user_id in {
            str(minute.get("responsible_user_id") or "").strip(),
            str(minute.get("created_by_user_id") or "").strip(),
        }:
            if not user_id:
                continue
            self.notifications.notify_minute_signed(
                user_id=user_id,
                minute_id=str(minute["id"]),
                minute_number=str(minute.get("minute_number") or ""),
                title=str(minute.get("title") or ""),
            )

    def _notify_managers_refused(
        self, minute: dict[str, Any], *, actor_name: str, reason: str
    ) -> None:
        for user_id in {
            str(minute.get("responsible_user_id") or "").strip(),
            str(minute.get("created_by_user_id") or "").strip(),
        }:
            if not user_id:
                continue
            self.notifications.notify_minute_refused(
                user_id=user_id,
                minute_id=str(minute["id"]),
                minute_number=str(minute.get("minute_number") or ""),
                title=str(minute.get("title") or ""),
                actor_name=actor_name,
                reason=reason,
            )

    def signature_image(self,user:Any,minute_id:str,signature_id:str)->bytes:
        minute=self._load(user,"view",minute_id); signature=self.repo.get_signature(minute_id,signature_id)
        if not signature: raise LookupError("Imagem de assinatura não encontrada.")
        return self.signature_storage.read(str(signature["image_path"]))

    def sign(self,user:Any,minute_id:str,*,png_bytes:bytes,display_name_confirmed:str,terms_accepted:bool,client_ip:str|None,user_agent:str|None,session_id:str|None,idempotency_key:str|None)->dict[str,Any]:
        minute=self._load(user,"sign",minute_id)
        if minute["status"] not in {"awaiting_signatures","partially_signed"}: raise ValueError("Ata não está aguardando assinaturas.")
        if not terms_accepted or not display_name_confirmed.strip(): raise ValueError("É necessário aceitar o termo e confirmar o nome do signatário.")
        signer=self.repo.get_signer_for_user(minute_id,self._user_id(user))
        if not signer: raise PermissionError("Você não é signatário desta ata.")
        version=self.repo.get_version(minute_id)
        if not version: raise LookupError("Versão não encontrada.")
        result=self.repo.register_signature(minute_id=minute_id,version_id=str(version["id"]),signer_id=str(signer["id"]),unit_code=str(minute["unit_code"]),user_id=self._user_id(user),display_name_confirmed=display_name_confirmed.strip(),content_hash=str(version["content_hash"]),image_path=self.signature_storage.save_png(unit_code=str(minute["unit_code"]),minute_id=minute_id,raw=png_bytes),terms_accepted=True,client_ip=client_ip,user_agent=user_agent,session_id=session_id,idempotency_key=idempotency_key,actor_user_id=self._user_id(user))
        if result.get("duplicate"): return {"signature":result["signature"],"minute":minute,"duplicate":True}
        new_status=MinuteStatusTransitionService.status_after_signature_progress(signed_count=result["signed_count"],required_count=result["required_count"])
        if new_status != minute["status"]: minute=self.repo.set_status(minute_id=minute_id,status=new_status,actor_user_id=self._user_id(user),action="signature_progress")
        if new_status == "signed":
            self._notify_managers_signed(minute)
        return {"signature":result["signature"],"minute":minute,"duplicate":False}

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
        minute = resolved["minute"]
        signer = resolved["signer"]
        invite = resolved["invite"]
        if not terms_accepted or not display_name_confirmed.strip():
            raise ValueError("É necessário aceitar o termo e confirmar o nome do signatário.")
        version = self.repo.get_version(str(minute["id"]))
        if not version:
            raise LookupError("Versão não encontrada.")
        actor_id = self._public_actor_id(signer, minute)
        uid = str(signer.get("user_id") or "").strip() or None
        result = self.repo.register_signature(
            minute_id=str(minute["id"]),
            version_id=str(version["id"]),
            signer_id=str(signer["id"]),
            unit_code=str(minute["unit_code"]),
            user_id=uid,
            display_name_confirmed=display_name_confirmed.strip(),
            content_hash=str(version["content_hash"]),
            image_path=self.signature_storage.save_png(
                unit_code=str(minute["unit_code"]),
                minute_id=str(minute["id"]),
                raw=png_bytes,
            ),
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
        if new_status == "signed":
            self._notify_managers_signed(minute)
        return {"signature": result["signature"], "minute": minute, "duplicate": False}

    def refuse(self,user:Any,minute_id:str,reason:str)->dict[str,Any]:
        minute=self._load(user,"sign",minute_id)
        if not reason.strip(): raise ValueError("Informe a justificativa da recusa.")
        signer=self.repo.get_signer_for_user(minute_id,self._user_id(user))
        if not signer: raise PermissionError("Você não é signatário desta ata.")
        self.repo.refuse_signature(minute_id=minute_id,signer_id=str(signer["id"]),reason=reason.strip(),actor_user_id=self._user_id(user),unit_code=str(minute["unit_code"]))
        updated=self.repo.set_status(minute_id=minute_id,status="in_review",actor_user_id=self._user_id(user),action="signature_refused")
        self._notify_managers_refused(
            updated,
            actor_name=str(signer.get("display_name") or "Signatário"),
            reason=reason.strip(),
        )
        return {"minute":updated}

    def public_refuse(self, raw_token: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("Informe a justificativa da recusa.")
        resolved = self.sign_invites.resolve(raw_token)
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
        self._notify_managers_refused(
            updated,
            actor_name=str(signer.get("display_name") or "Signatário"),
            reason=reason.strip(),
        )
        return {"minute": updated}

    def finalize(self,user:Any,minute_id:str)->dict[str,Any]:
        minute=self._load(user,"manage",minute_id)
        try: MinuteStatusTransitionService.assert_transition(minute["status"],"finalized")
        except MinuteStatusTransitionError as exc: raise ValueError(str(exc)) from exc
        version=self.repo.get_version(minute_id)
        if not version: raise LookupError("Versão não encontrada.")
        code=secrets.token_urlsafe(12); raw=self._render_pdf({**minute,"validation_code":code},version)
        return {"minute":self.repo.set_status(minute_id=minute_id,status="finalized",actor_user_id=self._user_id(user),action="finalize",extra={"final_pdf_path":self.pdf_storage.save(unit_code=str(minute["unit_code"]),minute_id=minute_id,raw=raw),"final_content_hash":version["content_hash"],"validation_code":code})}

    def _render_pdf(self,minute:dict[str,Any],version:dict[str,Any])->bytes:
        signatures=[{**s,"image_bytes":self.signature_storage.read(str(s["image_path"]))} for s in self.repo.list_signatures(str(minute["id"])) if s.get("image_path")]
        return self.pdf_renderer.render(minute,version,self.repo.list_participants(str(minute["id"])),self.repo.list_signers(str(minute["id"])),signatures)
    def export_pdf(self,user:Any,minute_id:str)->tuple[bytes,str]:
        minute=self._load(user,"view",minute_id); raw=self.pdf_storage.read(str(minute["final_pdf_path"])) if minute.get("final_pdf_path") else self._render_pdf(minute,self.repo.get_version(minute_id) or {})
        return raw,f"ata-transforma-mais-{str(minute['minute_number']).replace('/','-')}.pdf"
    def audit(self,user:Any,minute_id:str)->dict[str,Any]: self._load(user,"view",minute_id); return {"items":self.repo.list_audit(minute_id)}
    def soft_delete(self, user: Any, minute_id: str) -> dict[str, Any]:
        minute = self._load(user, "manage", minute_id)
        if not MinuteStatusTransitionService.can_delete(minute["status"]):
            raise ValueError("Atas assinadas ou finalizadas não podem ser excluídas.")
        return {"minute": self.repo.soft_delete(minute_id, self._user_id(user))}

    def cancel(self, user: Any, minute_id: str, reason: str | None = None) -> dict[str, Any]:
        minute = self._load(user, "manage", minute_id)
        try:
            MinuteStatusTransitionService.assert_transition(minute["status"], "cancelled")
        except MinuteStatusTransitionError as exc:
            raise ValueError(str(exc)) from exc
        return {
            "minute": self.repo.set_status(
                minute_id=minute_id,
                status="cancelled",
                actor_user_id=self._user_id(user),
                action="cancel",
                extra={"cancel_reason": (reason or "").strip() or None},
            )
        }

    def pending_signatures(self, user: Any) -> dict[str, Any]:
        return self.list_minutes(user, {"pending_for_me": True, "limit": 100, "offset": 0})
