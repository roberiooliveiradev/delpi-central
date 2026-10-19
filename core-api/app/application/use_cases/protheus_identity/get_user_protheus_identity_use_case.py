from __future__ import annotations

from uuid import UUID


class GetUserProtheusIdentityUseCase:
    def __init__(self, uow) -> None:
        self._uow = uow

    def execute(self, *, user_id: UUID) -> dict | None:
        user = self._uow.users.get_by_id(user_id)
        if not user:
            raise LookupError("Usuário não encontrado.")
        identity = self._uow.protheus_identities.get(user_id)
        return identity.to_dict() if identity else None
