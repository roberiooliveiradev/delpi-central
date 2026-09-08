from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """JWT identity only — never carries authorization decisions."""

    sub: str
    email: str
    name: str | None = None


@dataclass
class EffectiveUser:
    """Authorization context resolved from Core /me."""

    id: str
    email: str
    name: str | None
    permissions: set[str] = field(default_factory=set)
    is_superadmin: bool = False
    keycloak_sub: str | None = None
    access_token: str | None = None

    def has_permission(self, code: str) -> bool:
        if self.is_superadmin:
            return True
        return code in self.permissions
