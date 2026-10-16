"""Pending writes — bounded process-local orchestration state.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): when an
owner PREPARE capability returns a READY proposal (opaque
``proposal_ref``), DÉLIA holds the write context temporarily until a
typed bound decision (APPLY_PREPARED/REJECT_PREPARED) arrives on a
later turn. This store is orchestration state, NOT a
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

import time
from dataclasses import dataclass

from app.domain.governed_write.model import WriteProposalPreview


MAX_PENDING_WRITES = 128
# Fallback TTL when the owner payload carries no expiry — mirrors the
# delegated-token hard-cap convention; owner expiry wins when present.
DEFAULT_PENDING_TTL_SECONDS = 300.0

# C3-EXECUTION-SCOPE (§6.184): why a pending write awaits a bound typed
# decision. `execution_scope_choice` — the owner PREPARE declared no
# additional confirmation (explicit_user_confirmation=false), so the
# APPLY decision is the user's execution-scope choice only; it is NOT
# an owner confirmation and must not be reported to the owner as one.
# `execution_scope_plus_owner_confirmation` — the owner declared an
# explicit confirmation requirement, so the same bound APPLY decision
# satisfies BOTH the scope choice and the owner confirmation.
PENDING_PURPOSE_SCOPE_CHOICE = "execution_scope_choice"
PENDING_PURPOSE_SCOPE_PLUS_CONFIRMATION = (
    "execution_scope_plus_owner_confirmation"
)


@dataclass(frozen=True, slots=True)
class PendingWrite:
    """Backend-only pending write state.

    ``preview`` is always set: pending writes originate only from an
    owner PREPARE proposal whose ``proposal_ref`` is the raw owner
    handle — never serialized into any response, prompt, or log line.
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
    correlation_id: str = ""
    # Auditable pending purpose (§6.184): distinguishes an execution-
    # scope choice from a scope choice that also satisfies an owner-
    # declared confirmation. Empty for legacy/intent records.
    pending_purpose: str = ""


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
