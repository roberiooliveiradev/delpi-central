from __future__ import annotations

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser

CAPABILITY_FLAGS = {
    "portal": "supplies.portal.access",
    "purchaseRequests": "supplies.purchase-requests.access",
    "operations": "supplies.operations.access",
    "analytics": "supplies.analytics.access",
    "administration": "supplies.administration.manage",
    "viewAll": "supplies.purchase-requests.view-all",
    "export": "supplies.purchase-requests.export",
}

LEGACY_CAPABILITY_ALIASES = {
    "portal": (),
    "purchaseRequests": ("purchase-requests.access",),
    "operations": ("estoque-seguranca.access",),
    "analytics": ("dashboard-supplies.view", "idd-suprimentos.access"),
    "administration": ("purchase-requests.admin",),
    "viewAll": ("purchase-requests.view-all",),
    "export": ("purchase-requests.export",),
}


class CapabilityResolutionService:
    def __init__(self, authorization: AuthorizationService | None = None) -> None:
        self.authorization = authorization or AuthorizationService()

    def resolve(self, user: EffectiveUser) -> dict:
        flags = {}
        for flag, canonical in CAPABILITY_FLAGS.items():
            aliases = LEGACY_CAPABILITY_ALIASES.get(flag, ())
            flags[flag] = user.is_superadmin or user.has_permission(canonical) or any(
                user.has_permission(alias) for alias in aliases
            )

        return {
            "userId": user.id,
            "capabilities": flags,
            "allowedUnits": self.authorization.allowed_units(user),
            "aliasesDoNotGrantAppAccess": True,
        }
