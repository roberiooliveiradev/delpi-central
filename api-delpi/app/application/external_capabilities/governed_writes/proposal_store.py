"""In-process proposal store with HMAC-opaque handles.

Opaque handle format: ``base64url(proposal_id).base64url(hmac)``.
Full proposal body stays server-side (not model-trusted on ACT).

Topology note: api-delpi deploys as a single container running a single
uvicorn worker (``infra/docker-compose.yml`` / ``api-delpi/Dockerfile``),
so an in-process store is sufficient — same documented residual as the
sibling TÉO stack. A restart clears proposals: stale handles fail closed
(NOT_FOUND), never double-execute. Horizontal scaling of api-delpi
requires revisiting this store.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import threading
import time

from app.application.external_capabilities.governed_writes.errors import (
    INTERNAL,
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_EXPIRED,
    PROPOSAL_MISMATCH,
    PROPOSAL_NOT_FOUND,
    PROPOSAL_REQUIRED,

    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.proposal import (
    GovernedProposal,
)


# In-flight proposal cap. Expired entries are evicted first under pressure;
# beyond that the oldest proposals are evicted (they would fail closed as
# NOT_FOUND at ACT — never silently re-executed).
MAX_PROPOSALS = 1000


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _signing_key() -> bytes:
    # DAVI_GOVERNED_WRITE_HMAC_SECRET is MANDATORY — no fallback to shared
    # secrets (JWT_SECRET) or sibling surfaces (DAVI_CANDIDATE_HMAC_SECRET):
    # a fallback would let any holder of the broader secret forge write
    # proposals. Missing secret → fail-closed INTERNAL. READ tools never
    # reach this path, so a missing write secret never degrades reads.
    secret = (os.getenv("DAVI_GOVERNED_WRITE_HMAC_SECRET") or "").strip()
    if not secret:
        raise GovernedWriteError(
            "Governed write proposal secret (DAVI_GOVERNED_WRITE_HMAC_SECRET) "
            "is not configured.",
            code=INTERNAL,
            status_code=500,
        )
    return hashlib.sha256(f"davi-governed-proposal:{secret}".encode("utf-8")).digest()


def mint_proposal_handle(proposal_id: str) -> str:
    digest = hmac.new(
        _signing_key(), proposal_id.encode("utf-8"), hashlib.sha256
    ).digest()
    return f"{_b64(proposal_id.encode('utf-8'))}.{_b64(digest)}"


def parse_proposal_handle(handle: str) -> str:
    raw = (handle or "").strip()
    if not raw or "." not in raw:
        raise GovernedWriteError(
            "Invalid or missing proposal_handle.",
            code=PROPOSAL_NOT_FOUND,
            status_code=400,
        )
    left, right = raw.split(".", 1)
    try:
        proposal_id = _unb64(left).decode("utf-8")
        expected = hmac.new(
            _signing_key(), proposal_id.encode("utf-8"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _unb64(right)):
            raise ValueError("bad mac")
    except Exception as exc:
        raise GovernedWriteError(
            "Invalid proposal_handle.",
            code=PROPOSAL_NOT_FOUND,
            status_code=400,
        ) from exc
    return proposal_id


def resolve_proposal_handle(
    *,
    proposal_handle: str | None = None,
    proposal_id: str | None = None,
) -> str:
    """Canonical handle resolution for ACT entry points.

    ``proposal_id`` is an accepted recovery key: handles are a
    deterministic HMAC of the id, so re-minting feeds the same
    ``load_valid_proposal`` path (existence, expiry, consumed,
    actor binding, capability match) with zero auth logic duplicated.
    """
    handle = (proposal_handle or "").strip()
    if handle:
        return handle
    pid = (proposal_id or "").strip()
    if pid:
        return mint_proposal_handle(pid)
    raise GovernedWriteError(
        "proposal_handle or proposal_id is required for ACT.",
        code=PROPOSAL_REQUIRED,
        status_code=400,
    )


class ProposalStore:
    """Thread-safe TTL store. Single-process; single replica assumed."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: dict[str, GovernedProposal] = {}

    def put(self, proposal: GovernedProposal) -> str:
        with self._lock:
            self._purge_locked()
            if len(self._items) >= MAX_PROPOSALS:
                self._evict_for_capacity_locked()
            self._items[proposal.proposal_id] = proposal
            return mint_proposal_handle(proposal.proposal_id)

    def get(self, proposal_id: str) -> GovernedProposal | None:
        with self._lock:
            self._purge_locked()
            return self._items.get(proposal_id)

    def consume(self, proposal_id: str) -> None:
        with self._lock:
            item = self._items.get(proposal_id)
            if item is not None:
                item.consumed = True

    def take_for_act(
        self,
        proposal_id: str,
        *,
        actor_id: str,
        expected_capability: str | None,
    ) -> GovernedProposal:
        """Atomic validate+consume: a single critical section closes the
        check→consume race — two concurrent ACTs can never both pass on the
        same proposal."""
        with self._lock:
            self._purge_locked()
            proposal = self._items.get(proposal_id)
            if proposal is None:
                raise GovernedWriteError(
                    "Proposal not found or already consumed.",
                    code=PROPOSAL_NOT_FOUND,
                    status_code=404,
                )
            if proposal.expires_at < time.time():
                raise GovernedWriteError(
                    "Proposal expired. Prepare again.",
                    code=PROPOSAL_EXPIRED,
                    status_code=409,
                )
            if str(proposal.actor_id) != str(actor_id):
                raise GovernedWriteError(
                    "Proposal actor mismatch.",
                    code=PROPOSAL_ACTOR_MISMATCH,
                    status_code=403,
                )
            if expected_capability and proposal.capability != expected_capability:
                raise GovernedWriteError(
                    "Proposal capability mismatch.",
                    code=PROPOSAL_MISMATCH,
                    status_code=409,
                    data={
                        "expected": expected_capability,
                        "actual": proposal.capability,
                    },
                )
            # Consume now: the proposal leaves the store even if the owner
            # write later fails — replay can never silently re-execute.
            proposal.consumed = True
            self._items.pop(proposal_id, None)
            return proposal

    def _purge_locked(self) -> None:
        # Keep expired entries so ACT can report PROPOSAL_EXPIRED
        # (not silently NOT_FOUND). Consumed proposals are popped eagerly
        # by take_for_act, so nothing else is purged here.
        dead = [pid for pid, p in self._items.items() if p.consumed]
        for pid in dead:
            self._items.pop(pid, None)

    def _evict_for_capacity_locked(self) -> None:
        now = time.time()
        expired = [
            pid for pid, p in self._items.items() if p.expires_at < now
        ]
        for pid in expired:
            self._items.pop(pid, None)
        if len(self._items) >= MAX_PROPOSALS:
            oldest = sorted(
                self._items.values(), key=lambda p: p.created_at
            )
            for p in oldest[: len(self._items) - MAX_PROPOSALS + 1]:
                self._items.pop(p.proposal_id, None)


_STORE = ProposalStore()


def get_proposal_store() -> ProposalStore:
    return _STORE


def reset_proposal_store_for_tests() -> None:
    store = get_proposal_store()
    with store._lock:
        store._items.clear()
