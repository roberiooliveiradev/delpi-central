"""Schema/public-projection versioning and compatibility policy.

Three independent version axes (per the contract spec):

- ``SCHEMA_VERSION`` — Python contract + serialized profile shape.
- ``profile_version`` — per-profile content version owned by each MCP.
- ``PUBLIC_PROJECTION_VERSION`` — public exchange format version.

Policy: adding optional fields preserves consumers; breaking changes bump
major; unsupported versions fail explicitly, never silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import PUBLIC_PROJECTION_VERSION, SCHEMA_VERSION

CompatibilityStatus = Literal["SUPPORTED", "UNSUPPORTED"]


class IncompatibleVersionError(ValueError):
    """Raised when a payload declares a contract version this build cannot
    interpret. Explicit — callers must never downgrade silently."""


@dataclass(frozen=True)
class CompatibilityCheck:
    status: CompatibilityStatus
    declared_version: int
    supported_version: int
    axis: str
    message: str


def _check(declared: int, supported: int, axis: str) -> CompatibilityCheck:
    if declared == supported:
        return CompatibilityCheck(
            status="SUPPORTED",
            declared_version=declared,
            supported_version=supported,
            axis=axis,
            message="",
        )
    return CompatibilityCheck(
        status="UNSUPPORTED",
        declared_version=declared,
        supported_version=supported,
        axis=axis,
        message=(
            f"{axis} version {declared} is not supported by this contract "
            f"build (supports {supported}); migrate or upgrade explicitly."
        ),
    )


def check_schema_compatibility(declared_version: int) -> CompatibilityCheck:
    """Check a serialized profile's ``schema_version``."""
    return _check(int(declared_version), SCHEMA_VERSION, "schema")


def check_public_projection_compatibility(
    declared_version: int,
) -> CompatibilityCheck:
    """Check a received public profile's ``public_projection_version``."""
    return _check(
        int(declared_version), PUBLIC_PROJECTION_VERSION, "public_projection"
    )


def assert_schema_compatible(declared_version: int) -> None:
    """Fail fast when a payload's schema version is unsupported."""
    check = check_schema_compatibility(declared_version)
    if check.status != "SUPPORTED":
        raise IncompatibleVersionError(check.message)


def assert_public_projection_compatible(declared_version: int) -> None:
    """Fail fast when a public projection version is unsupported."""
    check = check_public_projection_compatibility(declared_version)
    if check.status != "SUPPORTED":
        raise IncompatibleVersionError(check.message)
