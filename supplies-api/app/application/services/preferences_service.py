from __future__ import annotations

from uuid import UUID

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.persistence.preferences_repository import PreferencesRepository

ALLOWED_DENSITIES = frozenset({"comfortable", "compact"})


class PreferencesService:
    def __init__(
        self,
        repository: PreferencesRepository | None = None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.repository = repository or PreferencesRepository()
        self.authorization = authorization or AuthorizationService()

    def get(self, user: EffectiveUser) -> dict:
        row = self.repository.get(UUID(user.id))
        if not row:
            return {
                "userId": user.id,
                "defaultBranch": None,
                "tableDensity": "comfortable",
            }
        return self._serialize(row)

    def patch(self, user: EffectiveUser, payload: dict) -> dict:
        current = self.get(user)
        default_branch = payload.get("defaultBranch", current["defaultBranch"])
        table_density = payload.get("tableDensity", current["tableDensity"])

        if table_density not in ALLOWED_DENSITIES:
            raise AuthorizationError("Invalid tableDensity")

        if default_branch is not None:
            self.authorization.require_unit(user, str(default_branch))

        row = self.repository.upsert(
            user_id=UUID(user.id),
            keycloak_sub=user.keycloak_sub,
            default_branch=default_branch,
            table_density=table_density,
        )
        return self._serialize(row)

    def _serialize(self, row: dict) -> dict:
        return {
            "userId": str(row["user_id"]),
            "defaultBranch": row.get("default_branch"),
            "tableDensity": row.get("table_density") or "comfortable",
        }
