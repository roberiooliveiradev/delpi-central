from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.get_user_access_profile_use_case import (
    GetUserAccessProfileUseCase,
)


class GetMyAccessProfileUseCase:
    """Wrapper fino para o titular em GET /me/access-profile."""

    def __init__(self, uow: UnitOfWork):
        self._delegate = GetUserAccessProfileUseCase(uow)

    def execute(self, user_id: UUID, *, is_superadmin: bool) -> dict[str, Any]:
        return self._delegate.execute(user_id, is_superadmin=is_superadmin)
