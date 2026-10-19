from __future__ import annotations

from uuid import UUID


class UpsertUserProtheusIdentityUseCase:
    def __init__(self, uow) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        user_id: UUID,
        actor_user_id: UUID | None,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
        ip_address: str | None = None,
    ) -> dict:
        user = self._uow.users.get_by_id(user_id)
        if not user:
            raise LookupError("Usuário não encontrado.")
        if not user.active and mapping_status == "mapped":
            raise ValueError("Não é permitido mapear usuário inativo.")

        previous = self._uow.protheus_identities.get(user_id)
        identity = self._uow.protheus_identities.upsert(
            user_id=user_id,
            protheus_user_id=protheus_user_id,
            protheus_user_code=protheus_user_code,
            mapping_status=mapping_status,
            mapping_source=mapping_source,
            verified=verified,
            updated_by_user_id=actor_user_id,
        )

        self._uow.audits.log(
            {
                "user_id": actor_user_id,
                "action": "protheus_identity.upsert",
                "entity_type": "user_protheus_identity",
                "entity_id": str(user_id),
                "payload": {
                    "before": previous.to_dict() if previous else None,
                    "after": identity.to_dict(),
                },
                "ip_address": ip_address,
            }
        )
        return identity.to_dict()
