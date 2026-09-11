"""Hardware identity resolution context for poll / continuity."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class HardwareIdentityOutcome(str, Enum):
    SAME_HARDWARE = "same_hardware"
    FIRST_OBSERVATION = "first_observation"
    HARDWARE_REPLACEMENT = "hardware_replacement"
    NETWORK_IDENTITY_CHANGED = "network_identity_changed"
    LEGACY_UNKNOWN = "legacy_unknown"


@dataclass(frozen=True)
class ObservedHardwareIdentity:
    hardware_uid: str | None = None
    controller_code: str | None = None
    mac_address: str | None = None
    identity_confidence: str = "legacy_unknown"
    identity_source: str = "legacy"
    firmware_version: str | None = None
    uptime_ms: int | None = None
    ip_address: str | None = None


@dataclass(frozen=True)
class HardwareResolutionResult:
    outcome: HardwareIdentityOutcome
    assignment_id: UUID | None
    hardware_unit_id: UUID | None
    previous_assignment_id: UUID | None = None
    previous_hardware_unit_id: UUID | None = None
    observed: ObservedHardwareIdentity = field(default_factory=ObservedHardwareIdentity)
    allow_counter_restore: bool = True
    replaced: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def same_hardware(self) -> bool:
        return self.outcome in {
            HardwareIdentityOutcome.SAME_HARDWARE,
            HardwareIdentityOutcome.NETWORK_IDENTITY_CHANGED,
        }
