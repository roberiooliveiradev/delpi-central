from __future__ import annotations

from uuid import UUID

from app.application.services.authorization_service import AuthorizationService
from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.application.services.preferences_service import PreferencesService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway
from app.infrastructure.persistence.preferences_repository import PreferencesRepository


class UserProfileService:
    """Compose Core identity + supplies preferences for WF-USER."""

    def __init__(
        self,
        *,
        preferences: PreferencesService | None = None,
        capabilities: CapabilityResolutionService | None = None,
        authorization: AuthorizationService | None = None,
        core_gateway: CoreApiHttpGateway | None = None,
        preferences_repository: PreferencesRepository | None = None,
    ) -> None:
        self.preferences = preferences or PreferencesService()
        self.capabilities = capabilities or CapabilityResolutionService()
        self.authorization = authorization or AuthorizationService()
        self.core_gateway = core_gateway or CoreApiHttpGateway()
        self.preferences_repository = (
            preferences_repository or PreferencesRepository()
        )

    def _assert_can_view(self, actor: EffectiveUser, target_user_id: str) -> None:
        target = (target_user_id or "").strip()
        if not target:
            raise AuthorizationError("Forbidden")
        if actor.id == target:
            self.authorization.require_permission(actor, "supplies.portal.access")
            return
        self.authorization.require_permission(actor, "supplies.administration.manage")

    def _assert_can_edit(self, actor: EffectiveUser, target_user_id: str) -> None:
        target = (target_user_id or "").strip()
        if not target or actor.id != target:
            raise AuthorizationError("Forbidden")
        self.authorization.require_permission(actor, "supplies.portal.access")

    def _identity_for(
        self,
        actor: EffectiveUser,
        target_user_id: str,
    ) -> dict[str, str]:
        target = target_user_id.strip()
        if actor.id == target:
            return {
                "userId": actor.id,
                "name": (actor.name or "").strip() or actor.email or actor.id,
                "email": actor.email or "",
            }

        token = actor.access_token or ""
        if token:
            try:
                found = self.core_gateway.lookup_directory_users(
                    access_token=token,
                    user_ids=[target],
                )
                hit = found.get(target)
                if hit:
                    return {
                        "userId": str(hit.get("id") or target),
                        "name": str(hit.get("name") or target),
                        "email": str(hit.get("email") or ""),
                    }
            except Exception:
                pass

        return {"userId": target, "name": target, "email": ""}

    def _preferences_for(self, user_id: str) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError as exc:
            raise AuthorizationError("Forbidden") from exc
        row = self.preferences_repository.get(uid)
        if not row:
            return {
                "userId": user_id,
                "defaultBranch": None,
                "tableDensity": "comfortable",
            }
        return {
            "userId": str(row["user_id"]),
            "defaultBranch": row.get("default_branch"),
            "tableDensity": row.get("table_density") or "comfortable",
        }

    def get(self, actor: EffectiveUser, target_user_id: str) -> dict:
        target = (target_user_id or "").strip()
        self._assert_can_view(actor, target)
        is_self = actor.id == target
        identity = self._identity_for(actor, target)
        preferences = (
            self.preferences.get(actor) if is_self else self._preferences_for(target)
        )

        payload: dict = {
            "userId": identity["userId"],
            "name": identity["name"],
            "email": identity["email"],
            "isSelf": is_self,
            "preferences": preferences,
            "capabilities": None,
            "allowedUnits": [],
        }
        if is_self:
            caps = self.capabilities.resolve(actor)
            payload["capabilities"] = caps["capabilities"]
            payload["allowedUnits"] = caps["allowedUnits"]
        return payload

    def patch(self, actor: EffectiveUser, target_user_id: str, payload: dict) -> dict:
        target = (target_user_id or "").strip()
        self._assert_can_edit(actor, target)
        prefs_patch = payload.get("preferences") if isinstance(payload, dict) else None
        if prefs_patch is None and isinstance(payload, dict):
            prefs_patch = {
                key: payload[key]
                for key in ("defaultBranch", "tableDensity")
                if key in payload
            }
        if not isinstance(prefs_patch, dict):
            prefs_patch = {}
        self.preferences.patch(actor, prefs_patch)
        return self.get(actor, target)
