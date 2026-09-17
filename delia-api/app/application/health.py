from __future__ import annotations

from typing import Mapping


def build_liveness_status(*, service_name: str, service_version: str) -> dict[str, str]:
    """Process liveness only. Must not report unimplemented dependencies."""
    return {
        "status": "available",
        "service": service_name,
        "version": service_version,
    }


def health_claims_unimplemented_dependency(payload: Mapping[str, object]) -> bool:
    forbidden = {
        "database",
        "db",
        "core",
        "core_api",
        "domain",
        "llm",
        "provider",
        "providers",
        "automation_hub",
        "jwt",
        "ready",
        "dependencies",
    }
    lowered = {str(key).lower() for key in payload.keys()}
    return bool(lowered & forbidden)
