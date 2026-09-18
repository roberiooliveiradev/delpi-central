from __future__ import annotations

from app.application.security.supplies_permissions import (
    has_canonical_access,
    has_canonical_manage,
)
from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser


class CapabilityResolutionService:
    def __init__(self, authorization: AuthorizationService | None = None) -> None:
        self.authorization = authorization or AuthorizationService()

    def resolve(self, user: EffectiveUser) -> dict:
        flags = {
            "access": user.is_superadmin or has_canonical_access(user),
            "manage": user.is_superadmin or has_canonical_manage(user),
        }
        return {
            "userId": user.id,
            "capabilities": flags,
            "allowedUnits": self.authorization.allowed_units(user),
        }
