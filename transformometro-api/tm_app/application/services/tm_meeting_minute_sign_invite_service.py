"""Convites de assinatura por magic link (token hasheado)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from tm_app.application.services.token_service import generate_public_token, hash_token
from tm_app.config import settings

logger = logging.getLogger("transformometro.atas.sign_invites")


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

    def resolve(self, raw_token: str) -> dict[str, Any]:
        token = str(raw_token or "").strip()
        if not token:
            raise LookupError("Convite de assinatura não encontrado.")
        invite = self.repo.get_invite_by_token_hash(hash_token(token))
        if not invite:
            raise LookupError("Convite de assinatura não encontrado.")
        if invite.get("consumed_at"):
            raise ValueError("Este link de assinatura já foi utilizado.")
        expires_at = invite.get("expires_at")
        if isinstance(expires_at, datetime):
            exp = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                raise ValueError("Este link de assinatura expirou.")
        signer = self.repo.get_signer(str(invite["signer_id"]))
        if not signer:
            raise LookupError("Signatário não encontrado.")
        if signer.get("status") not in {"pending", "viewed"}:
            raise ValueError("Signatário não está elegível para assinar.")
        minute = self.repo.get_minute(str(invite["minute_id"]))
        if not minute or minute.get("deleted_at"):
            raise LookupError("Ata não encontrada.")
        if minute.get("status") not in {"awaiting_signatures", "partially_signed"}:
            raise ValueError("Ata não está aguardando assinaturas.")
        return {"invite": invite, "signer": signer, "minute": minute}

    def consume(self, invite_id: str) -> dict[str, Any] | None:
        return self.repo.consume_invite(invite_id)
