"""Resolve Core-authoritative effective platform access for a Keycloak subject (S2S)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.services.permission_resolver import PermissionResolver


class EffectiveAccessIdentityNotFoundError(Exception):
    """Keycloak subject is not linked to a Core user (no email fallback)."""


class EffectiveAccessUnavailableError(Exception):
    """Permission resolution backend failed."""


@dataclass(frozen=True)
class EffectiveAccessResult:
    user_id: UUID
    keycloak_subject: UUID
    permissions: list[str]
    is_superadmin: bool


class GetEffectiveAccessBySubjectUseCase:
    """
    Owner: core-api.

    Resolves effective permissions via PermissionResolver for a Core user whose
    primary key equals the Keycloak ``sub`` (UUID). Does not accept caller-supplied
    permissions and does not fall back to email identity.
    """

    def __init__(self, uow) -> None:
        self._uow = uow

    def execute(self, *, keycloak_subject: UUID) -> EffectiveAccessResult:
        user = self._uow.users.get_by_id(keycloak_subject)
        if user is None:
            raise EffectiveAccessIdentityNotFoundError(
                f"No Core user linked to Keycloak subject {keycloak_subject}"
            )

        is_superadmin = bool(user.is_superadmin)
        try:
            permissions = PermissionResolver(
                self._uow.permission_queries,
                self._uow.cache,
            ).resolve(user.id, is_superadmin)
        except Exception as exc:  # noqa: BLE001 — surface as unavailable to callers
            raise EffectiveAccessUnavailableError(str(exc)) from exc

        if not isinstance(permissions, list):
            raise EffectiveAccessUnavailableError(
                "PermissionResolver returned a non-list payload"
            )

        return EffectiveAccessResult(
            user_id=user.id,
            keycloak_subject=keycloak_subject,
            permissions=[str(code) for code in permissions],
            is_superadmin=is_superadmin,
        )
