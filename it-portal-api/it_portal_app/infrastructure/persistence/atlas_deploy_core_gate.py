"""ATLAS P2.2h.2v: real fresh Core RBAC observation, not PREPARE authority.

Private, non-routable diagnostics. Only the trusted JWT middleware may build
the actor/token; caller fields themselves do not authenticate anyone.
load_user_rbac(force_refresh=True) bypasses cached and stale Core grants.
A granted permission is evidence of a lookup, never an authorization to write,
approve or deploy. No Core permission is registered or provisioned here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable
from uuid import UUID

from delpi_auth.middleware.fastapi_auth import load_user_rbac

ACCESS = "it-portal.access"
DEPLOY_VIEW = "it-portal.deploy.view"
DEPLOY_PREPARE = "it-portal.deploy.prepare"
_REQUIRED = frozenset((ACCESS, DEPLOY_VIEW, DEPLOY_PREPARE))
_TOKEN_MAX = 16384
_CLOCK_SKEW = timedelta(seconds=5)
_UUID_RE = re.compile(r"[0-9a-f-]{36}\Z")


class AtlasCoreGateError(Exception):
    """Finite codes only; never leak JWT, Core body, subject, or grants."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class TrustedHumanActor:
    """Projection exclusively from a validated human JWT middleware context."""

    subject: str
    principal_type: str
    access_token: str


@dataclass(frozen=True, slots=True)
class FreshCoreGrantObservation:
    """Fresh Core grant lookup, never an ACT/PREPARE ticket."""

    subject: str
    checked_at: datetime
    required_grants_present: bool = True
    prepare_eligible: bool = False
    can_execute: bool = False


def _valid_uuid4(value: object) -> bool:
    if type(value) is not str or _UUID_RE.fullmatch(value) is None:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _aware(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


class FreshCorePrepareInspector:
    """No HTTP route. Injecting Core loader is for tests/trusted DI ONLY."""

    def __init__(
        self, *,
        fetch_rbac: Callable[..., Awaitable[dict]] = load_user_rbac,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        enabled: bool = False,
    ):
        self._fetch = fetch_rbac
        self._clock = clock
        self._enabled = enabled is True

    async def read(self, *, actor: TrustedHumanActor) -> FreshCoreGrantObservation:
        if not self._enabled:
            raise AtlasCoreGateError("ATLAS_CORE_INSPECTION_DISABLED")
        if (
            type(actor) is not TrustedHumanActor
            or actor.principal_type != "user"
            or not _valid_uuid4(actor.subject)
            or type(actor.access_token) is not str
            or not 1 <= len(actor.access_token) <= _TOKEN_MAX
            or actor.access_token.strip() != actor.access_token
        ):
            raise AtlasCoreGateError("ATLAS_CORE_IDENTITY_DENIED")
        try:
            # Exactly one authoritative Core lookup, explicitly no cached
            # or stale fallback. This must not run on a private asyncio loop.
            rbac = await self._fetch(actor.access_token, force_refresh=True)
        except Exception:
            raise AtlasCoreGateError("ATLAS_CORE_UNAVAILABLE") from None
        if type(rbac) is not dict or not _valid_uuid4(rbac.get("id")):
            raise AtlasCoreGateError("ATLAS_CORE_RESPONSE_INVALID")
        if rbac["id"] != actor.subject:
            raise AtlasCoreGateError("ATLAS_CORE_IDENTITY_MISMATCH")
        grants = rbac.get("permissions")
        if (
            type(grants) not in (list, tuple)
            or not all(type(p) is str for p in grants)
            or len(grants) > 1024
        ):
            raise AtlasCoreGateError("ATLAS_CORE_RESPONSE_INVALID")
        # No role wildcard, inherited admin power or is_superadmin bypass.
        if not _REQUIRED.issubset(set(grants)):
            raise AtlasCoreGateError("ATLAS_CORE_EXPLICIT_GRANT_MISSING")
        observed = self._clock()
        if not _aware(observed):
            raise AtlasCoreGateError("ATLAS_CORE_CLOCK_INVALID")
        return FreshCoreGrantObservation(
            subject=actor.subject,
            checked_at=observed.astimezone(timezone.utc),
        )
