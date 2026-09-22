"""In-process proposal store with HMAC-opaque handles for VISTA GPT Actions.

Opaque handle format: ``base64url(proposal_id).base64url(hmac)``.
Full proposal body stays server-side (not model-trusted on COMMIT).

Runtime suitability: single-process / sticky single replica → ACCEPT_WITH_RESIDUAL.
Review trigger: workers > 1, replicas > 1, or cross-process prepare/commit.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import threading
import time

from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal import VistaProposal
from tv_app.config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _signing_key() -> bytes:
    secret = (settings.JWT_SECRET or "").strip() or "tv-dashboard-gpt-proposal"
    return hashlib.sha256(f"tv-vista-proposal:{secret}".encode("utf-8")).digest()


def mint_proposal_handle(proposal_id: str) -> str:
    digest = hmac.new(
        _signing_key(), proposal_id.encode("utf-8"), hashlib.sha256
    ).digest()
    return f"{_b64(proposal_id.encode('utf-8'))}.{_b64(digest)}"


def parse_proposal_handle(handle: str) -> str:
    raw = (handle or "").strip()
    if not raw or "." not in raw:
        raise GptActionsError(
            "proposal_handle inválido ou ausente.",
            code="PROPOSAL_NOT_FOUND",
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
        raise GptActionsError(
            "proposal_handle inválido.",
            code="PROPOSAL_NOT_FOUND",
            status_code=400,
        ) from exc
    return proposal_id


class ProposalStore:
    """Thread-safe TTL store. Single-process; sticky/single replica assumed."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: dict[str, VistaProposal] = {}

    def put(self, proposal: VistaProposal) -> str:
        with self._lock:
            self._purge_locked()
            self._items[proposal.proposal_id] = proposal
            return mint_proposal_handle(proposal.proposal_id)

    def get(self, proposal_id: str) -> VistaProposal | None:
        with self._lock:
            self._purge_locked()
            return self._items.get(proposal_id)

    def consume(self, proposal_id: str) -> None:
        with self._lock:
            item = self._items.get(proposal_id)
            if item is not None:
                item.consumed = True

    def _purge_locked(self) -> None:
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
) -> VistaProposal:
    proposal_id = parse_proposal_handle(proposal_handle)
    proposal = get_proposal_store().get(proposal_id)
    if proposal is None:
        raise GptActionsError(
            "Proposta não encontrada ou já consumida.",
            code="PROPOSAL_NOT_FOUND",
            status_code=404,
        )
    if proposal.consumed:
        raise GptActionsError(
            "Proposta já consumida. Refaça o preview.",
            code="PROPOSAL_CHANGED",
            status_code=409,
        )
    if proposal.expires_at < time.time():
        raise GptActionsError(
            "Proposta expirada. Refaça o preview.",
            code="PROPOSAL_EXPIRED",
            status_code=409,
        )
    if str(proposal.actor_id) != str(actor_id):
        raise GptActionsError(
            "Proposta pertence a outro ator.",
            code="AUTHZ_DENIED",
            status_code=403,
        )
    if expected_capability and proposal.capability != expected_capability:
        raise GptActionsError(
            "Proposta não corresponde à capability esperada.",
            code="PROPOSAL_CHANGED",
            status_code=409,
            details={
                "expected": expected_capability,
                "actual": proposal.capability,
            },
        )
    return proposal
