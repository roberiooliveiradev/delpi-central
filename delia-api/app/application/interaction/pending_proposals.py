"""Pending writes — bounded process-local orchestration state.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): when an
owner PREPARE capability returns a READY proposal (opaque
``proposal_ref``), or a direct-ACT intent awaits confirmation, DÉLIA
holds the write context temporarily until a structured confirmation
arrives on a later turn. This store is orchestration state, NOT a
capability registry: it never records whether a capability exists or is
enabled — capability availability is always re-read live from the
owner ``tools/list`` at commit time.

The raw ``proposal_ref`` is security-sensitive owner material: it stays
backend-only (never in the model context, the HTTP response, the MFE or
logs). The store is keyed by a non-reversible digest and entries expire
with the owner-declared expiry plus a bounded fallback TTL;
confirmation consumes the entry (single use).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.domain.governed_write.model import WriteProposalPreview


MAX_PENDING_WRITES = 128
# Fallback TTL when the owner payload carries no expiry — mirrors the
# delegated-token hard-cap convention; owner expiry wins when present.
DEFAULT_PENDING_TTL_SECONDS = 300.0


def intent_digest(
    group_key: str, remote_capability: str, arguments: Mapping[str, Any]
) -> str:
    """Non-reversible identity for a direct-ACT pending intent."""
    canonical = json.dumps(
        {
            "group_key": group_key,
            "remote_capability": remote_capability,
            "arguments": dict(arguments),
        },
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PendingWrite:
    """Backend-only pending write state.

    ``preview`` is set for PREPARE-originated proposals (its
    ``proposal_ref`` is the raw owner handle — never serialized into any
    response, prompt, or log line). ``intent_arguments`` is set for
    direct-ACT intents awaiting generic confirmation.
    """

    digest: str
    capability_ref: str
    group_key: str
    actor_user_id: str
    session_id: str
    expires_at_epoch: float
    created_at_epoch: float
    preview: WriteProposalPreview | None = None
    act_remote_capability: str | None = None
    intent_remote_capability: str | None = None
    intent_arguments: Mapping[str, Any] | None = None
    correlation_id: str = ""


class PendingWriteStore:
    """In-memory bounded store keyed by non-reversible digest."""

    def __init__(self, *, max_entries: int = MAX_PENDING_WRITES) -> None:
        self._max = max_entries
        self._items: dict[str, PendingWrite] = {}

    def put(self, record: PendingWrite) -> None:
        self._evict_expired(time.time())
        if len(self._items) >= self._max:
            # Bounded: evict oldest first rather than growing unbounded.
            oldest = min(
                self._items,
                key=lambda k: self._items[k].created_at_epoch,
            )
            del self._items[oldest]
        self._items[record.digest] = record

    def get(self, digest: str) -> PendingWrite | None:
        record = self._items.get(str(digest or "").strip())
        if record is None:
            return None
        if record.expires_at_epoch <= time.time():
            del self._items[record.digest]
            return None
        return record

    def take(self, digest: str) -> PendingWrite | None:
        """Single-use consume: a confirmed/rejected write is removed."""
        record = self.get(digest)
        if record is not None:
            del self._items[record.digest]
        return record

    def _evict_expired(self, now_epoch: float) -> None:
        expired = [
            key
            for key, record in self._items.items()
            if record.expires_at_epoch <= now_epoch
        ]
        for key in expired:
            del self._items[key]
