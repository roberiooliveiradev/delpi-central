"""Deterministic plan digest binding PREPARE → ACT for GPT commits."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_plan_digest(
    *,
    actor_id: str,
    target: dict[str, Any] | None,
    ops: list[Any],
    catalog_version: str,
    base_revision: int | None,
) -> str:
    payload = {
        "actorId": str(actor_id or "").strip(),
        "target": target if isinstance(target, dict) else {},
        "ops": ops if isinstance(ops, list) else [],
        "catalogVersion": str(catalog_version or "").strip(),
        "baseRevision": base_revision if base_revision is None else int(base_revision),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return digest


def compute_request_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def digests_match(left: str, right: str) -> bool:
    a = str(left or "").strip().encode("utf-8")
    b = str(right or "").strip().encode("utf-8")
    if len(a) != len(b):
        return False
    return hmac.compare_digest(a, b)
