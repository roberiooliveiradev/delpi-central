from __future__ import annotations

from app.application.security.supplies_permissions import (
    can_view_all_purchase_requests,
    has_canonical_access,
    has_canonical_manage,
)
from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser


class CapabilityResolutionService:
    def __init__(self, authorization: AuthorizationService | None = None) -> None:
        self.authorization = authorization or AuthorizationService()

    def resolve(self, user: EffectiveUser) -> dict:
        if user.is_superadmin:
            flags = {"access": True, "manage": True, "viewAll": True}
        else:
            flags = {
                "access": has_canonical_access(user),
                "manage": has_canonical_manage(user),
                "viewAll": can_view_all_purchase_requests(user),
            }
        return {
            "userId": user.id,
            "capabilities": flags,
            "allowedUnits": self.authorization.allowed_units(user),
        }
