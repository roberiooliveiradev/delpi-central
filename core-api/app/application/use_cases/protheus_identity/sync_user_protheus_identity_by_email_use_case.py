from __future__ import annotations

from uuid import UUID

from app.domain.services.protheus_user_candidate_resolver import (
    pick_protheus_user_candidate,
)
from app.infrastructure.gateways.delpi_protheus_users_gateway import (
    DelpiProtheusUsersGateway,
    TotvsLookupUnavailableError,
)


class SyncUserProtheusIdentityByEmailUseCase:
    """Sync Protheus identity using authoritative Core user email (not client body)."""

    def __init__(
        self,
        uow,
        *,
        gateway: DelpiProtheusUsersGateway | None = None,
    ) -> None:
        self._uow = uow
        self._gateway = gateway or DelpiProtheusUsersGateway()

    def execute(
        self,
        *,
        user_id: UUID,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
    ) -> dict:
        user = self._uow.users.get_by_id(user_id)
        if not user:
            raise LookupError("Usuário não encontrado.")
        if not user.active:
            raise ValueError("Não é permitido sincronizar usuário inativo.")

        normalized_email = (user.email or "").strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise ValueError("Usuário sem e-mail válido para sincronização.")

        try:
            lookup = self._gateway.get_protheus_user_by_email(normalized_email)
        except TotvsLookupUnavailableError:
            raise
        except LookupError:
            raise

        protheus_user = lookup.get("user")
        if lookup.get("ambiguous"):
            candidates = lookup.get("candidates") or []
            protheus_user = pick_protheus_user_candidate(
                candidates,
                portal_user_name=user.name,
            )
            if not protheus_user:
                # Do not silently pick the first candidate; leave prior mapping intact.
                raise LookupError(
                    "Mais de um usuário Protheus com este e-mail. "
                    "Não foi possível desambiguar pelo nome do portal."
                )
        elif not lookup.get("found") or not protheus_user:
            raise LookupError(
                "Nenhum usuário Protheus com USR_EMAIL igual ao e-mail do portal."
            )

        # Keep USR_ID as string — preserve leading zeros.
        protheus_user_id = str(protheus_user.get("protheus_user_id") or "").strip()
        if not protheus_user_id:
            raise LookupError("Usuário Protheus retornado sem USR_ID.")

        identity = self._uow.protheus_identities.upsert(
            user_id=user_id,
            protheus_user_id=protheus_user_id,
            protheus_user_code=protheus_user.get("code"),
            mapping_status="mapped",
            mapping_source="email_match",
            verified=True,
            updated_by_user_id=actor_user_id,
        )
        self._uow.audits.log(
            {
                "user_id": actor_user_id,
                "action": "protheus_identity.sync_by_email",
                "entity_type": "user_protheus_identity",
                "entity_id": str(user_id),
                "payload": {
                    "protheus_user_id": protheus_user_id,
                    "verified": True,
                    "email_domain": normalized_email.split("@")[-1],
                },
                "ip_address": ip_address,
            }
        )
        return {
            "mapping": identity.to_dict(),
            "protheus_user": {
                "protheus_user_id": protheus_user_id,
                "code": protheus_user.get("code"),
                "name": protheus_user.get("name"),
                "email": protheus_user.get("email") or normalized_email,
            },
            "synced_by_email": normalized_email,
        }
