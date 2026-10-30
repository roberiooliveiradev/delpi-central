"""CAIO governed proposals — server-side sealed handles.

Padrão TÉO/VISTA/EVA (governed_writes) reimplementado sob o owner
Commercial — o plano proíbe import de internals de outros bounded
contexts; aqui o modelo é mínimo e deliberado:

- Proposta selada fica server-side; o modelo só carrega o handle
  opaco ``base64url(id).base64url(hmac)`` — nunca o corpo da
  operação, portanto não pode adulterar alvo/impacto/versão.
- Handle vinculado a ``actor_id`` (humano autenticado), capability
  (entity.action) e ``target_ref`` — proposta de outro ator ou de
  outro alvo é rejeitada (replay/cross-user/cross-target).
- TTL curto + uso único (``consumed``): commit reutilizado falha
  honestamente.
- Store em processo, single-replica — mesma premissa documentada do
  TÉO; réplica múltipla exigiria store compartilhado (decisão
  futura, não implementada aqui).

``confirmed=true`` informado pelo modelo NÃO é prova de confirmação
para destrutivas — só o handle selado + verificação server-side.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

PROPOSAL_TTL_ENV = "CAIO_PROPOSAL_TTL_SECONDS"
_DEFAULT_TTL_SECONDS = 15 * 60


class CaioProposalError(Exception):
    """Typed proposal failure — mapped to honest MCP errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass
class CaioProposal:
    """Sealed server-side write proposal (never model-mutable)."""

    proposal_id: str
    capability: str  # e.g. "task.delete"
    actor_id: str
    target_ref: str | None
    change_fingerprint: str  # sha256 of the exact change payload
    impact: dict[str, Any]
    validation_result: dict[str, Any]
    expected_postcondition: dict[str, Any]
    created_at: float
    expires_at: float
    consumed: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "capability": self.capability,
            "target_ref": self.target_ref,
            "impact": self.impact,
            "validation_result": self.validation_result,
            "expected_postcondition": self.expected_postcondition,
            "expires_at": self.expires_at,
            "confirmation_requirement": (
                "Apresente exatamente este resumo ao usuário humano e, "
                "somente após autorização explícita, execute phase=commit "
                "com o proposal_ref devolvido — o handle é verificado no "
                "servidor contra ator, alvo, expiração e uso único."
            ),
        }


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _signing_key() -> bytes:
    secret = (
        (os.getenv("KEYCLOAK_AUDIENCE") or "").strip()
        or (os.getenv("SERVICE_NAME") or "commercial-api")
    )
    return hashlib.sha256(
        f"caio-governed-proposal:{secret}".encode("utf-8")
    ).digest()


def mint_proposal_handle(proposal_id: str) -> str:
    digest = hmac.new(
        _signing_key(), proposal_id.encode("utf-8"), hashlib.sha256
    ).digest()
    return f"{_b64(proposal_id.encode('utf-8'))}.{_b64(digest)}"


def parse_proposal_handle(handle: str) -> str:
    raw = (handle or "").strip()
    if not raw or "." not in raw:
        raise CaioProposalError(
            "proposal_ref inválido ou ausente.",
            code="proposal_not_found",
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
        raise CaioProposalError(
            "proposal_ref inválido.",
            code="proposal_not_found",
            status_code=400,
        ) from exc
    return proposal_id


class ProposalStore:
    """Thread-safe TTL store. Single-process; single replica assumed."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: dict[str, CaioProposal] = {}

    def put(self, proposal: CaioProposal) -> str:
        with self._lock:
            self._purge_locked()
            self._items[proposal.proposal_id] = proposal
            return mint_proposal_handle(proposal.proposal_id)

    def get(self, proposal_id: str) -> CaioProposal | None:
        with self._lock:
            self._purge_locked()
            return self._items.get(proposal_id)

    def consume(self, proposal_id: str) -> None:
        with self._lock:
            item = self._items.get(proposal_id)
            if item is not None:
                item.consumed = True

    def _purge_locked(self) -> None:
        # Keep expired entries so commit can report PROPOSAL_EXPIRED
        # honestly; only consumed proposals are removed.
        dead = [pid for pid, p in self._items.items() if p.consumed]
        for pid in dead:
            self._items.pop(pid, None)


_STORE = ProposalStore()


def proposal_ttl_seconds() -> int:
    try:
        return max(60, int(os.getenv(PROPOSAL_TTL_ENV, _DEFAULT_TTL_SECONDS)))
    except (TypeError, ValueError):
        return _DEFAULT_TTL_SECONDS


def get_proposal_store() -> ProposalStore:
    return _STORE


def reset_proposal_store_for_tests() -> None:
    store = get_proposal_store()
    with store._lock:
        store._items.clear()


def seal_proposal(
    *,
    capability: str,
    actor_id: str,
    target_ref: str | None,
    change: dict[str, Any],
    impact: dict[str, Any],
    validation_result: dict[str, Any] | None = None,
    expected_postcondition: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> tuple[CaioProposal, str]:
    """Seal a governed write proposal and return (proposal, handle)."""
    now = time.time()
    proposal = CaioProposal(
        proposal_id=str(uuid.uuid4()),
        capability=capability,
        actor_id=str(actor_id),
        target_ref=target_ref,
        change_fingerprint=fingerprint(change),
        impact=impact,
        validation_result=validation_result or {},
        expected_postcondition=expected_postcondition or {},
        created_at=now,
        expires_at=now + proposal_ttl_seconds(),
        meta=meta or {},
    )
    handle = get_proposal_store().put(proposal)
    return proposal, handle


def load_valid_proposal(
    *,
    proposal_handle: str,
    actor_id: str,
    expected_capability: str,
    expected_target_ref: str | None = None,
) -> CaioProposal:
    """Verify handle integrity + actor + capability + target + freshness."""
    proposal_id = parse_proposal_handle(proposal_handle)
    proposal = get_proposal_store().get(proposal_id)
    if proposal is None:
        raise CaioProposalError(
            "Proposta não encontrada ou já consumida.",
            code="proposal_not_found",
            status_code=404,
        )
    if proposal.consumed:
        raise CaioProposalError(
            "Proposta já consumida — prepare novamente.",
            code="proposal_stale",
            status_code=409,
        )
    if proposal.expires_at < time.time():
        raise CaioProposalError(
            "Proposta expirada — prepare novamente.",
            code="proposal_expired",
            status_code=409,
        )
    if str(proposal.actor_id) != str(actor_id):
        raise CaioProposalError(
            "Proposta pertence a outro ator.",
            code="proposal_actor_mismatch",
            status_code=403,
        )
    if proposal.capability != expected_capability:
        raise CaioProposalError(
            "Proposta não corresponde à operação solicitada.",
            code="proposal_mismatch",
            status_code=409,
            detail={
                "expected": expected_capability,
                "actual": proposal.capability,
            },
        )
    if (
        expected_target_ref is not None
        and proposal.target_ref != expected_target_ref
    ):
        raise CaioProposalError(
            "Proposta foi selada para outro alvo.",
            code="proposal_mismatch",
            status_code=409,
            detail={
                "expected_target": expected_target_ref,
                "actual_target": proposal.target_ref,
            },
        )
    return proposal
