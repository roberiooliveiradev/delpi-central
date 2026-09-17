from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PlatformAccessContext:
    """Authoritative platform access projection consumed by DÉLIA.

    Effective permissions/roles/groups/is_superadmin MUST come from Core.
    JWT is identity transport only — never final permission authority.
    """

    user_id: str
    name: str
    email: str
    roles: tuple[str, ...] = ()
    groups: tuple[str, ...] = ()
    effective_permissions: tuple[str, ...] = ()
    is_superadmin: bool = False
    source: str = "CORE"


def platform_access_from_core_me(payload: Mapping[str, object]) -> PlatformAccessContext:
    """Build context from Core GET /me. Ignores any JWT-local permission claims."""
    user_id = str(payload.get("id") or "").strip()
    email = str(payload.get("email") or "").strip()
    name = str(payload.get("name") or "").strip() or email or "User"
    if not user_id or not email:
        raise ValueError("Core /me missing required identity fields")

    return PlatformAccessContext(
        user_id=user_id,
        name=name,
        email=email,
        roles=_string_tuple(payload.get("roles")),
        groups=_string_tuple(payload.get("groups")),
        effective_permissions=_string_tuple(payload.get("permissions")),
        is_superadmin=bool(payload.get("is_superadmin", False)),
        source="CORE",
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("Core /me field must be a list of strings")
    return tuple(str(item) for item in value)
