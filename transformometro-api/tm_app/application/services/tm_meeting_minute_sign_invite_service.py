"""Convites de assinatura por magic link (token hasheado)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from tm_app.application.services.token_service import generate_public_token, hash_token
from tm_app.config import settings

logger = logging.getLogger("transformometro.atas.sign_invites")

_ELIGIBLE_SIGNER_STATUSES = frozenset({"pending", "viewed"})
_AWAITING_MINUTE_STATUSES = frozenset({"awaiting_signatures", "partially_signed"})

_MSG_NOT_FOUND = "Convite de assinatura não encontrado."
_MSG_CONSUMED = "Este link de assinatura já foi utilizado."
_MSG_EXPIRED = "Este link de assinatura expirou."
_MSG_SIGNER_MISSING = "Signatário não encontrado."
_MSG_MINUTE_MISSING = "Ata não encontrada."
_MSG_MINUTE_NOT_AWAITING = "Ata não está aguardando assinaturas."
_MSG_ALREADY_SIGNED = "Esta assinatura já foi registrada."
_MSG_REFUSED = "Esta assinatura foi recusada."
_MSG_CANCELLED = "Este convite de assinatura foi cancelado."
_MSG_REVISED = (
    "Esta ata foi revisada. Solicite um novo envio do link de assinatura."
)
_MSG_NOT_ELIGIBLE = "Signatário não está elegível para assinar."


class SignInviteRepository(Protocol):
    def invalidate_open_invites(self, *, signer_id: str) -> int: ...

    def create_invite(
        self,
        *,
        signer_id: str,
        minute_id: str,
        unit_code: str,
        token_hash: str,
        expires_at: datetime,
    ) -> dict[str, Any]: ...

    def get_invite_by_token_hash(self, token_hash: str) -> dict[str, Any] | None: ...

    def consume_invite(self, invite_id: str) -> dict[str, Any] | None: ...

    def rebind_invite_signer(self, *, invite_id: str, signer_id: str) -> dict[str, Any] | None: ...

    def find_eligible_signer_match(
        self,
        *,
        minute_id: str,
        user_id: str | None,
        invite_email: str | None,
    ) -> dict[str, Any] | None: ...

    def get_signer(self, signer_id: str) -> dict[str, Any] | None: ...

    def get_minute(self, minute_id: str) -> dict[str, Any] | None: ...


class TmMeetingMinuteSignInviteService:
    def __init__(
        self,
        repo: SignInviteRepository,
        *,
        ttl_days: int | None = None,
        public_base_url: str | None = None,
    ) -> None:
        self.repo = repo
        self.ttl_days = int(
            ttl_days
            if ttl_days is not None
            else settings.TM_ATA_SIGN_INVITE_TTL_DAYS
        )
        self.public_base_url = (
            public_base_url
            if public_base_url is not None
            else (settings.PUBLIC_BASE_URL or "")
        ).rstrip("/")

    def build_public_sign_url(self, raw_token: str) -> str:
        path = f"/p/transformometro/sign/{raw_token}"
        if self.public_base_url:
            return f"{self.public_base_url}{path}"
        return path

    def issue(self, *, signer: dict[str, Any], minute: dict[str, Any]) -> dict[str, Any]:
        signer_id = str(signer["id"])
        minute_id = str(minute["id"])
        unit_code = str(minute.get("unit_code") or signer.get("unit_code") or "")
        self.repo.invalidate_open_invites(signer_id=signer_id)
        raw = generate_public_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        invite = self.repo.create_invite(
            signer_id=signer_id,
            minute_id=minute_id,
            unit_code=unit_code,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
        return {
            "invite": invite,
            "raw_token": raw,
            "sign_url": self.build_public_sign_url(raw),
            "expires_at": expires_at,
        }

    @staticmethod
    def _message_for_ineligible_signer(status: str | None) -> str:
        key = str(status or "").strip().lower()
        if key == "signed":
            return _MSG_ALREADY_SIGNED
        if key == "refused":
            return _MSG_REFUSED
        if key == "cancelled":
            return _MSG_CANCELLED
        if key == "invalidated":
            return _MSG_REVISED
        return _MSG_NOT_ELIGIBLE

    def _try_remap_stale_signer(
        self,
        *,
        invite: dict[str, Any],
        signer: dict[str, Any],
        minute: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Se a ata foi reenviada, reassocia o token ao signatário elegível atual."""
        if minute.get("status") not in _AWAITING_MINUTE_STATUSES:
            return None
        match = self.repo.find_eligible_signer_match(
            minute_id=str(minute["id"]),
            user_id=str(signer.get("user_id") or "").strip() or None,
            invite_email=str(signer.get("invite_email") or "").strip() or None,
        )
        if not match:
            return None
        if str(match["id"]) == str(signer["id"]):
            return match
        rebound = self.repo.rebind_invite_signer(
            invite_id=str(invite["id"]),
            signer_id=str(match["id"]),
        )
        if rebound:
            invite.update(rebound)
        logger.info(
            "sign_invite_rebound invite_id=%s from_signer=%s to_signer=%s minute_id=%s",
            invite.get("id"),
            signer.get("id"),
            match.get("id"),
            minute.get("id"),
        )
        return match

    def resolve(self, raw_token: str) -> dict[str, Any]:
        token = str(raw_token or "").strip()
        if not token:
            raise LookupError(_MSG_NOT_FOUND)
        invite = self.repo.get_invite_by_token_hash(hash_token(token))
        if not invite:
            raise LookupError(_MSG_NOT_FOUND)

        minute = self.repo.get_minute(str(invite["minute_id"]))
        if not minute or minute.get("deleted_at"):
            raise LookupError(_MSG_MINUTE_MISSING)

        signer = self.repo.get_signer(str(invite["signer_id"]))
        if not signer:
            raise LookupError(_MSG_SIGNER_MISSING)

        status = str(signer.get("status") or "")
        if status == "signed":
            return {
                "invite": invite,
                "signer": signer,
                "minute": minute,
                "outcome": "already_signed",
            }

        if invite.get("consumed_at"):
            raise ValueError(_MSG_CONSUMED)

        expires_at = invite.get("expires_at")
        if isinstance(expires_at, datetime):
            exp = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                raise ValueError(_MSG_EXPIRED)

        current_version_id = str(minute.get("current_version_id") or "")
        signer_version_id = str(signer.get("version_id") or "")
        stale_version = bool(
            current_version_id
            and signer_version_id
            and current_version_id != signer_version_id
        )

        if status not in _ELIGIBLE_SIGNER_STATUSES or stale_version:
            remapped = self._try_remap_stale_signer(
                invite=invite, signer=signer, minute=minute
            )
            if remapped and remapped.get("status") in _ELIGIBLE_SIGNER_STATUSES:
                signer = remapped
            else:
                if status == "refused":
                    raise ValueError(_MSG_REFUSED)
                if stale_version or status == "invalidated":
                    raise ValueError(_MSG_REVISED)
                if minute.get("status") not in _AWAITING_MINUTE_STATUSES:
                    raise ValueError(_MSG_MINUTE_NOT_AWAITING)
                raise ValueError(self._message_for_ineligible_signer(status))

        if minute.get("status") not in _AWAITING_MINUTE_STATUSES:
            raise ValueError(_MSG_MINUTE_NOT_AWAITING)
        return {"invite": invite, "signer": signer, "minute": minute}

    def consume(self, invite_id: str) -> dict[str, Any] | None:
        return self.repo.consume_invite(invite_id)
