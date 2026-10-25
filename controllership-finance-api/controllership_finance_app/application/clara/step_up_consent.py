"""CLARA — consentimento verificável por superfície confiável.

Uma chamada MCP feita pelo assistente, mesmo com JWT válido, não
comprova que o usuário humano consentiu (Doc 106 §3.1). O
consentimento exige prova física fora do canal do modelo:

- **Modo A — HOST_ATTESTED**: atestação HMAC do host (quando
  configurado via ``CLARA_HOST_ATTESTATION_SECRET``);
- **Modo B — portal_step_up**: rota BFF ``/clara-batches/{id}/consent``
  / ``/clara-proposals/{id}/consent`` chamada pelo Portal MFE com um
  access token Keycloak emitido **depois** do PREPARE
  (``iat >= created_at``). O refresh token que produz esse JWT novo
  vive na sessão do Portal — o access token do canal MCP não se
  renova, logo o assistente não consegue fabricar essa credencial.

Este módulo valida a frescura do token e grava ``consent_record``
via os repositórios canônicos — nunca pelo caminho MCP.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.clara_batch_repository import (
    BatchActorMismatch,
    BatchNotConfirmed,
    ClaraBatchRepository,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
    ProposalActorMismatch,
)

CONSENT_TYPE_PORTAL_STEP_UP = "portal_step_up"
CONSENT_TYPE_HOST_ATTESTED = "host_attested_intent"

# Folga para dessincronia de relógio Keycloak ↔ PostgreSQL.
_STEP_UP_CLOCK_SKEW_SECONDS = 10
_STEP_UP_FUTURE_IAT_TOLERANCE_SECONDS = 60


class ConsentRequired(ChecklistDomainError):
    code = "consent_required"
    status = 403


class StepUpTokenStale(ChecklistDomainError):
    code = "step_up_token_stale"
    status = 403


def clara_consent_url(*, batch_id: str | None = None,
                      proposal_id: str | None = None) -> str:
    """Deep link da superfície confiável de consentimento no Portal."""
    if batch_id:
        return (
            "/apps/controllership-finance/closing/clara-consent"
            f"?batch={batch_id}"
        )
    return (
        "/apps/controllership-finance/closing/clara-consent"
        f"?proposal={proposal_id}"
    )


def _epoch(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(
        str(value)
    )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def assert_step_up_token(
    claims: dict, *, prepared_at: Any
) -> dict:
    """Exige token emitido depois do PREPARE — prova de sessão fresca.

    O access token MCP do assistente antecede o PREPARE (a sessão de
    chat já existia quando o plano foi selado) e não pode ser
    renovado pelo modelo. Um token com ``iat >= created_at`` só é
    obtido pela sessão Keycloak do Portal (refresh ou re-login) —
    evidência física de presença humana na superfície confiável.
    """
    iat = claims.get("iat")
    if iat is None:
        raise StepUpTokenStale(
            "Token sem iat — consentimento não verificável."
        )
    prepared_epoch = _epoch(prepared_at)
    now_epoch = datetime.now(timezone.utc).timestamp()
    if float(iat) < prepared_epoch - _STEP_UP_CLOCK_SKEW_SECONDS:
        raise StepUpTokenStale(
            "Token anterior à preparação — atualize a sessão no "
            "Portal (refresh) e confirme pela página de "
            "consentimento."
        )
    if float(iat) > now_epoch + _STEP_UP_FUTURE_IAT_TOLERANCE_SECONDS:
        raise StepUpTokenStale(
            "Token com iat futuro — relógio fora de sincronia."
        )
    return {
        "token_iat": int(float(iat)),
        "token_jti": claims.get("jti"),
        "token_sub": claims.get("sub"),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class ClaraStepUpConsent:
    """Consentimento por superfície confiável (Portal + token fresco)."""

    def __init__(
        self,
        *,
        batches: ClaraBatchRepository | None = None,
        proposals: ClaraProposalRepository | None = None,
    ) -> None:
        self._batches = batches or ClaraBatchRepository()
        self._proposals = proposals or ClaraProposalRepository()

    # -- batch ----------------------------------------------------------

    def batch_summary(self, *, batch_id: str, actor_sub: str) -> dict:
        batch = self._batches.get_batch(batch_id=batch_id)
        if batch["actor_sub"] != actor_sub:
            raise BatchActorMismatch("Lote pertence a outro ator.")
        plan = batch.get("plan") or {}
        if isinstance(plan, str):
            import json as _json
            plan = _json.loads(plan)
        return {
            "batch_id": batch_id,
            "status": batch["status"],
            "plan_hash": batch["plan_hash"],
            "consent_mode": batch["consent_mode"],
            "expires_at": _iso(batch["expires_at"]),
            "created_at": _iso(batch["created_at"]),
            "operations": [
                {
                    "seq": op["seq"],
                    "capability": op["capability"],
                    "resource_type": op["resource_type"],
                    "resource_key": op["resource_key"],
                    "state": op["state"],
                    "depends_on": op.get("depends_on") or [],
                }
                for op in batch.get("operations", [])
            ],
        }

    def record_batch_consent(
        self, *, batch_id: str, actor_sub: str, token_claims: dict
    ) -> dict:
        batch = self._batches.get_batch(batch_id=batch_id)
        if batch["actor_sub"] != actor_sub:
            raise BatchActorMismatch("Lote pertence a outro ator.")
        if batch["status"] != "PREPARED":
            raise BatchNotConfirmed(
                f"Lote em estado {batch['status']} — não aceita "
                "consentimento."
            )
        expires = _epoch(batch["expires_at"])
        if expires < datetime.now(timezone.utc).timestamp():
            raise ConsentRequired("Lote expirado — reprepare o plano.")
        proof = assert_step_up_token(
            token_claims, prepared_at=batch["created_at"]
        )
        consent_record = {
            "type": CONSENT_TYPE_PORTAL_STEP_UP,
            "confirmed_by": actor_sub,
            "plan_hash": batch["plan_hash"],
            "expires_at": _iso(batch["expires_at"]),
            "recorded_at": _now_iso(),
            **proof,
        }
        updated = self._batches.record_consent_by_id(
            batch_id=batch_id,
            actor_sub=actor_sub,
            plan_hash=batch["plan_hash"],
            mode="CONSOLIDATED",
            consent_record=consent_record,
        )
        return {
            "batch_id": batch_id,
            "status": updated["status"],
            "consent_mode": "CONSOLIDATED",
            "confirmed_at": _iso(updated["confirmed_at"]),
        }

    # -- proposal --------------------------------------------------------

    def proposal_summary(self, *, proposal_id: str,
                         actor_sub: str) -> dict:
        proposal = self._proposals.get_by_id(proposal_id=proposal_id)
        if proposal["actor_sub"] != actor_sub:
            raise ProposalActorMismatch(
                "Proposta pertence a outro ator."
            )
        return {
            "proposal_id": proposal_id,
            "capability": proposal["capability"],
            "resource_type": proposal["resource_type"],
            "resource_key": proposal["resource_key"],
            "params": proposal["payload"],
            "expected_state": proposal["expected_state"],
            "execution_state": proposal["execution_state"],
            "consented_at": (
                _iso(proposal["consented_at"])
                if proposal.get("consented_at") else None
            ),
            "expires_at": _iso(proposal["expires_at"]),
            "created_at": _iso(proposal["created_at"]),
        }

    def record_proposal_consent(
        self, *, proposal_id: str, actor_sub: str,
        token_claims: dict
    ) -> dict:
        proposal = self._proposals.get_by_id(proposal_id=proposal_id)
        if proposal["actor_sub"] != actor_sub:
            raise ProposalActorMismatch(
                "Proposta pertence a outro ator."
            )
        if proposal["batch_operation_id"] is not None:
            raise ConsentRequired(
                "Proposta pertence a um lote — consinta o lote na "
                "página de consentimento."
            )
        expires = _epoch(proposal["expires_at"])
        if expires < datetime.now(timezone.utc).timestamp():
            raise ConsentRequired(
                "Proposta expirada — reprepare a operação."
            )
        proof = assert_step_up_token(
            token_claims, prepared_at=proposal["created_at"]
        )
        consent_record = {
            "type": CONSENT_TYPE_PORTAL_STEP_UP,
            "confirmed_by": actor_sub,
            "capability": proposal["capability"],
            "resource_key": proposal["resource_key"],
            "expires_at": _iso(proposal["expires_at"]),
            "recorded_at": _now_iso(),
            **proof,
        }
        updated = self._proposals.record_consent(
            proposal_id=proposal_id,
            actor_sub=actor_sub,
            consent_record=consent_record,
        )
        return {
            "proposal_id": proposal_id,
            "consented_at": _iso(updated["consented_at"]),
        }
