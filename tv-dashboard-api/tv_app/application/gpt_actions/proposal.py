"""Opaque governed proposal for VISTA GPT write PREPARE → COMMIT."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

DEFAULT_TTL_SECONDS = 15 * 60
CAPABILITY_PRESENTATION_CHANGE = "presentation_change"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass
class VistaProposal:
    proposal_id: str
    capability: str
    actor_id: str
    resource_type: str | None
    resource_id: str | None
    current_state_fingerprint: str
    exact_change: dict[str, Any]
    confirmation_requirement: dict[str, Any]
    risk: str | None
    confirmation_policy: str
    catalog_version: str
    base_revision: int | None
    created_at: float
    expires_at: float
    content_hash: str
    consumed: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "confirmation_requirement": self.confirmation_requirement,
            "risk": self.risk,
            "confirmation_policy": self.confirmation_policy,
            "catalog_version": self.catalog_version,
            "base_revision": self.base_revision,
            "expires_at": self.expires_at,
            "current_state_fingerprint": self.current_state_fingerprint,
            "exact_change": {
                "target": self.exact_change.get("target"),
                "ops": self.exact_change.get("ops"),
                "operationNames": self.exact_change.get("operationNames"),
            },
        }

    def to_store_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_store_dict(cls, data: dict[str, Any]) -> VistaProposal:
        return cls(**data)


def new_proposal_id() -> str:
    return f"vp_{uuid.uuid4().hex}"


def create_proposal(
    *,
    actor_id: str,
    target: dict[str, Any],
    ops: list[dict[str, Any]],
    operation_names: list[str],
    catalog_version: str,
    base_revision: int | None,
    risk: str | None,
    confirmation_policy: str,
    side_effect_hints: list[str] | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    meta: dict[str, Any] | None = None,
) -> VistaProposal:
    now = time.time()
    playlist_id = str((target or {}).get("playlistId") or "").strip() or None
    policy = str(confirmation_policy or "direct").strip().lower()
    confirmation_requirement = {
        "explicit_user_confirmation": True,
        "confirmation_policy": policy,
        "requires_confirmed_true": True,
        "destructive": policy == "confirm",
    }
    exact_change = {
        "target": target if isinstance(target, dict) else {},
        "ops": ops if isinstance(ops, list) else [],
        "operationNames": operation_names,
        "catalogVersion": str(catalog_version or "").strip(),
        "baseRevision": base_revision if base_revision is None else int(base_revision),
        "sideEffectHints": list(side_effect_hints or []),
    }
    state_fp = fingerprint(
        {
            "playlistId": playlist_id,
            "baseRevision": base_revision if base_revision is None else int(base_revision),
            "catalogVersion": str(catalog_version or "").strip(),
        }
    )
    content_hash = fingerprint(
        {
            "capability": CAPABILITY_PRESENTATION_CHANGE,
            "actor_id": str(actor_id),
            "resource_id": playlist_id,
            "state": state_fp,
            "exact_change": exact_change,
        }
    )
    return VistaProposal(
        proposal_id=new_proposal_id(),
        capability=CAPABILITY_PRESENTATION_CHANGE,
        actor_id=str(actor_id),
        resource_type="playlist" if playlist_id else "playlist_create",
        resource_id=playlist_id,
        current_state_fingerprint=state_fp,
        exact_change=exact_change,
        confirmation_requirement=confirmation_requirement,
        risk=risk,
        confirmation_policy=policy,
        catalog_version=str(catalog_version or "").strip(),
        base_revision=base_revision if base_revision is None else int(base_revision),
        created_at=now,
        expires_at=now + max(60, int(ttl_seconds)),
        content_hash=content_hash,
        meta=meta or {},
    )
