"""In-process proposal store with HMAC-opaque handles.

Opaque handle format: ``base64url(proposal_id).base64url(hmac)``.
Full proposal body stays server-side (not model-trusted on ACT).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import threading
import time
from typing import Any

from tm_app.application.governed_writes.errors import (
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_EXPIRED,
    PROPOSAL_MISMATCH,
    PROPOSAL_NOT_FOUND,
    PROPOSAL_STALE,
    GovernedWriteError,
)
from tm_app.application.governed_writes.proposal import GovernedProposal
from tm_app.config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _signing_key() -> bytes:
    secret = (
        (settings.JWT_SECRET or "").strip()
        or (getattr(settings, "KEYCLOAK_AUDIENCE", None) or "transformometro")
    )
    return hashlib.sha256(f"tm-governed-proposal:{secret}".encode("utf-8")).digest()


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


class ProposalStore:
    """Thread-safe TTL store. Single-process; sticky/single replica assumed."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: dict[str, GovernedProposal] = {}

    def put(self, proposal: GovernedProposal) -> str:
        with self._lock:
            self._purge_locked()
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

    def _purge_locked(self) -> None:
        # Keep expired entries so load_valid_proposal can return PROPOSAL_EXPIRED
        # (not silently NOT_FOUND). Remove only consumed proposals.
        dead = [pid for pid, p in self._items.items() if p.consumed]
        for pid in dead:
            self._items.pop(pid, None)


_STORE = ProposalStore()


def get_proposal_store() -> ProposalStore:
    return _STORE


def reset_proposal_store_for_tests() -> None:
    store = get_proposal_store()
    with store._lock:
        store._items.clear()


def load_valid_proposal(
    *,
    proposal_handle: str,
    actor_id: str,
    expected_capability: str | None = None,
) -> GovernedProposal:
    proposal_id = parse_proposal_handle(proposal_handle)
    proposal = get_proposal_store().get(proposal_id)
    if proposal is None:
        raise GovernedWriteError(
            "Proposal not found or already consumed.",
            code=PROPOSAL_NOT_FOUND,
            status_code=404,
        )
    if proposal.consumed:
        raise GovernedWriteError(
            "Proposal already consumed.",
            code=PROPOSAL_STALE,
            status_code=409,
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
            data={"expected": expected_capability, "actual": proposal.capability},
        )
    return proposal
