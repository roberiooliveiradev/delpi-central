from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.protheus_users.protheus_users_repository import (
    ProtheusUsersRepository,
)


class GetProtheusUserByEmailUseCase:
    def __init__(self, repository: ProtheusUsersRepository | None = None) -> None:
        self._repository = repository or ProtheusUsersRepository()

    def execute(self, email: str) -> dict[str, Any]:
        matches = self._repository.find_by_email(email)
        if not matches:
            return {"found": False, "match_count": 0, "user": None}
        if len(matches) > 1:
            return {
                "found": False,
                "match_count": len(matches),
                "user": None,
                "ambiguous": True,
                "candidates": matches,
            }
        return {"found": True, "match_count": 1, "user": matches[0], "ambiguous": False}
