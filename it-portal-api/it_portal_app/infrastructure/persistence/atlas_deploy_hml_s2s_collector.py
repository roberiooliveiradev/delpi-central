"""ATLAS P2.2h.2y: HML-only Keycloak S2S identity for a pinned collector.

Uses the existing shared ServiceTokenValidator (real JWT issuer/signature,
expiry and audience checks) with a dedicated allowlisted client and scope.
A valid S2S token proves a Keycloak *client*, not the operating system,
container, Git checkout, Docker engine, mTLS channel or an ACT authority.

Private, default OFF. No route, OAuth client registration, HTTP call to
the collector, secret, credential provisioning, Docker access or DB write.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import (
    ServiceTokenValidator, ServiceTokenValidatorConfig,
)

from .atlas_deploy_host_receipt_bridge import PinnedHostTarget

_SCOPE = "it-portal.atlas.hml.observe"
_CLIENT = re.compile(r"itp-atlas-hml-[a-z0-9-]{4,48}\Z")
_HOST = re.compile(r"[a-z0-9][a-z0-9_.-]{1,100}\Z")
_AUDIENCE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9:._/-]{2,127}\Z")
_TOKEN_MAX = 16384
_SKEW = timedelta(seconds=5)
_MAX_TOKEN_REMAINING = timedelta(minutes=15)


class AtlasCollectorIdentityError(Exception):
    """Safe finite error codes, never echo token, issuer or raw JWT claims."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLCollectorIdentityPolicy:
    """Only a trusted server-side owner may construct or configure this."""

    host_id: str
    client_id: str
    audience: str


@dataclass(frozen=True, slots=True)
class HMLCollectorClientObservation:
    """JWT client binding only. All deployment and OS trust flags stay OFF."""

    client_id: str
    host_id: str
    observed_at: datetime
    token_expires_at: datetime
    scope: str = _SCOPE
    keycloak_client_verified: bool = True
    host_process_attested: bool = False
    transport_mutual_auth_attested: bool = False
    checkout_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _aware(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


class HMLCollectorS2SVerifier:
    """Validate a real service token, not a user-supplied ServiceIdentity.

    Caller is a future backend adapter that obtains an independently verified
    S2S Authorization header. The token must NOT originate from a human JWT
    or an LLM/MCP input. In tests, patch the shared JWT decoder only.
    """

    def __init__(
        self, *,
        policy: HMLCollectorIdentityPolicy,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        enabled: bool = False,
    ):
        self._policy = policy
        self._clock = clock
        self._enabled = enabled is True
        self._validator: ServiceTokenValidator | None = None
        if (
            type(policy) is HMLCollectorIdentityPolicy
            and type(policy.host_id) is str
            and _HOST.fullmatch(policy.host_id) is not None
            and type(policy.client_id) is str
            and _CLIENT.fullmatch(policy.client_id) is not None
            and type(policy.audience) is str
            and _AUDIENCE.fullmatch(policy.audience) is not None
        ):
            self._validator = ServiceTokenValidator(
                ServiceTokenValidatorConfig(
                    audience=policy.audience,
                    allowed_clients=frozenset((policy.client_id,)),
                )
            )

    def verify(
        self, *, service_token: str, host: PinnedHostTarget,
    ) -> HMLCollectorClientObservation:
        if not self._enabled:
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_DISABLED")
        if self._validator is None:
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_CONFIG_INVALID")
        if (
            type(host) is not PinnedHostTarget
            or host.environment != "hml"
            or host.service_id != "public-hub"
            or host.compose_project != "delpi-hml"
            or host.container_name != "delpi-hml-public-hub"
            or host.host_id != self._policy.host_id
            or type(service_token) is not str
            or not 1 <= len(service_token) <= _TOKEN_MAX
            or service_token.strip() != service_token
        ):
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_TARGET_DENIED")

        now = self._clock()
        if not _aware(now):
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_CLOCK_INVALID")

        try:
            identity = self._validator.validate(
                service_token,
                required_scopes=(_SCOPE,),
                allowed_clients=(self._policy.client_id,),
            )
        except Exception:
            # Never leak any JWT/JWKS/Keycloak detail through the diagnostic.
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_DENIED") from None
        if (
            type(identity) is not ServiceIdentity
            or identity.principal_type != "service"
            or identity.client_id != self._policy.client_id
            or not identity.subject
            or not identity.issuer
            or self._policy.audience not in identity.audience
            or _SCOPE not in identity.scopes
            or type(identity.expires_at) is not int
            or not 0 < identity.expires_at < 4102444800
        ):
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_CLAIMS_INVALID")
        try:
            expires = datetime.fromtimestamp(identity.expires_at, tz=timezone.utc)
        except (OverflowError, ValueError, OSError):
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_CLAIMS_INVALID") from None
        remaining = expires - now.astimezone(timezone.utc)
        if remaining <= _SKEW or remaining > _MAX_TOKEN_REMAINING:
            raise AtlasCollectorIdentityError("ATLAS_COLLECTOR_S2S_LIFETIME_DENIED")
        return HMLCollectorClientObservation(
            client_id=identity.client_id,
            host_id=self._policy.host_id,
            observed_at=now.astimezone(timezone.utc),
            token_expires_at=expires,
        )
