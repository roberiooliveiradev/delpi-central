from __future__ import annotations

from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_portal_user_manage,
)
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


class GetPortalUserProtheusMappingUseCase:
    def __init__(self, repository: UserProtheusMappingRepository | None = None) -> None:
        self._repository = repository or UserProtheusMappingRepository()

    def execute(self, *, actor, user_id: str) -> dict[str, Any]:
        if not has_portal_user_manage(actor):
            raise PermissionError("Sem permissão para gerenciar usuários do portal.")
        mapping = self._repository.get_mapping(user_id)
        return {"mapping": mapping}

