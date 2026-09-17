"""Governed write proposal model + fingerprint helpers."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_TTL_SECONDS = 15 * 60


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass
class GovernedProposal:
    proposal_id: str
    capability: str
    actor_id: str
    actor_email: str | None
    resource_type: str | None
    resource_id: str | None
    current_state_fingerprint: str
    exact_change: dict[str, Any]
    validation_result: dict[str, Any]
    consequential_impact: dict[str, Any]
    confirmation_requirement: dict[str, Any]
    expected_postcondition: dict[str, Any]
    created_at: float
    expires_at: float
    content_hash: str
    consumed: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "capability": self.capability,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "validation_result": self.validation_result,
            "consequential_impact": self.consequential_impact,
            "confirmation_requirement": self.confirmation_requirement,
            "expected_postcondition": self.expected_postcondition,
            "expires_at": self.expires_at,
            "current_state_fingerprint": self.current_state_fingerprint,
            "exact_change": self.exact_change,
        }

    def to_store_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_store_dict(cls, data: dict[str, Any]) -> GovernedProposal:
        return cls(**data)


def new_proposal_id() -> str:
    return f"gp_{uuid.uuid4().hex}"


def build_content_hash(
    *,
    capability: str,
    actor_id: str,
    resource_type: str | None,
    resource_id: str | None,
    current_state_fingerprint: str,
    exact_change: dict[str, Any],
) -> str:
    return fingerprint(
        {
            "capability": capability,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "current_state_fingerprint": current_state_fingerprint,
            "exact_change": exact_change,
        }
    )


def create_proposal(
    *,
    capability: str,
    actor_id: str,
    actor_email: str | None,
    resource_type: str | None,
    resource_id: str | None,
    current_state_fingerprint: str,
    exact_change: dict[str, Any],
    validation_result: dict[str, Any],
    consequential_impact: dict[str, Any],
    confirmation_requirement: dict[str, Any],
    expected_postcondition: dict[str, Any],
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    meta: dict[str, Any] | None = None,
) -> GovernedProposal:
    now = time.time()
    content_hash = build_content_hash(
        capability=capability,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        current_state_fingerprint=current_state_fingerprint,
        exact_change=exact_change,
    )
    return GovernedProposal(
        proposal_id=new_proposal_id(),
        capability=capability,
        actor_id=str(actor_id),
        actor_email=actor_email,
        resource_type=resource_type,
        resource_id=resource_id,
        current_state_fingerprint=current_state_fingerprint,
        exact_change=exact_change,
        validation_result=validation_result,
        consequential_impact=consequential_impact,
        confirmation_requirement=confirmation_requirement,
        expected_postcondition=expected_postcondition,
        created_at=now,
        expires_at=now + max(60, int(ttl_seconds)),
        content_hash=content_hash,
        meta=meta or {},
    )
