from __future__ import annotations

from app.application.security.supplies_permissions import (
    can_administer,
    can_enter_shell,
    can_export_purchase_requests,
    can_use_analytics,
    can_use_operations,
    can_use_portal,
    can_use_purchase_requests,
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
            flags = {
                "access": True,
                "manage": True,
                "portal": True,
                "purchaseRequests": True,
                "operations": True,
                "analytics": True,
                "administration": True,
                "viewAll": True,
                "export": True,
                "shell": True,
            }
        else:
            access = has_canonical_access(user)
            manage = has_canonical_manage(user)
            administration = can_administer(user)
            flags = {
                "access": access,
                "manage": manage or administration,
                "portal": access or can_use_portal(user),
                "purchaseRequests": access or can_use_purchase_requests(user),
                "operations": access or can_use_operations(user),
                "analytics": access or can_use_analytics(user),
                "administration": administration,
                "viewAll": can_view_all_purchase_requests(user),
                "export": access or can_export_purchase_requests(user),
                "shell": can_enter_shell(user),
            }
        return {
            "userId": user.id,
            "capabilities": flags,
            "allowedUnits": self.authorization.allowed_units(user),
            "aliasesDoNotGrantAppAccess": True,
            "deprecatedCapabilityFlags": [
                "portal",
                "purchaseRequests",
                "operations",
                "analytics",
                "administration",
                "export",
            ],
        }
