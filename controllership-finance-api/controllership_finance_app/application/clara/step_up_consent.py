"""CLARA — consentimento verificável por superfície confiável.

R-CLARA-01 (Doc 106): uma chamada MCP feita pelo assistente, mesmo
com JWT válido, não comprova que o usuário humano consentiu — e a
idade do access token, sozinha, também não é prova de aprovação do
plano. A prova é um objeto de autorização emitido pelo servidor:

- **Desafio de consentimento** (`clara_consent_challenge`, V014):
  emitido no PREPARE e vinculado a ator, alvo, `plan_hash`/
  `plan_version`, expiração, origem `portal` e correlação. A página
  do Portal apresenta o plano selado e devolve o `challenge_id`;
  a rota BFF só grava `consent_record` dentro da mesma transação que
  marca o desafio APPROVED — com token Keycloak emitido depois do
  desafio (``iat >= challenge.created_at``), credencial que o canal
  MCP não consegue fabricar porque o refresh token vive na sessão do
  Portal. A execução consome o desafio — nenhum consentimento serve
  a outro lote, outro plano, outro ator ou segunda execução;
- **Modo A — HOST_ATTESTED**: atestação HMAC do host (quando
  configurado via ``CLARA_HOST_ATTESTATION_SECRET``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from controllership_finance_app.application.clara.operation_presentation import (
    period_label,
    present_operation,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.clara_batch_repository import (
    BatchActorMismatch,
    BatchNotConfirmed,
    ClaraBatchRepository,
)
from controllership_finance_app.infrastructure.persistence.clara_consent_challenge_repository import (
    ClaraConsentChallengeRepository,
    ConsentChallengeMismatch,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
    ProposalActorMismatch,
)

CONSENT_TYPE_PORTAL_STEP_UP = "portal_step_up"
CONSENT_TYPE_HOST_ATTESTED = "host_attested_intent"

# Folga para dessincronia de relógio Keycloak ↔ PostgreSQL. O iat é
# controle SECUNDÁRIO de frescor da sessão — a prova primária é o
# desafio aprovado e vinculado ao plano, não a idade do token.
_STEP_UP_CLOCK_SKEW_SECONDS = 10
_STEP_UP_FUTURE_IAT_TOLERANCE_SECONDS = 60

_BLOCK_REASON_PT = {
    "unknown_capability": "Operação não reconhecida pela CLARA.",
    "missing_params": "Dados obrigatórios ausentes para esta operação.",
    "snapshot_unavailable": (
        "O estado atual do recurso não pôde ser confirmado — a "
        "operação ficou bloqueada por segurança."
    ),
}


class ConsentRequired(ChecklistDomainError):
    code = "consent_required"
    status = 403


class StepUpTokenStale(ChecklistDomainError):
    code = "step_up_token_stale"
    status = 403


class ConsentChallengeRequired(ChecklistDomainError):
    code = "consent_challenge_required"
    status = 400


class ConsentNotDisplayable(ChecklistDomainError):
    code = "consent_not_displayable"
    status = 409


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


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      default=str)


def proposal_plan_hash(
    capability: str, payload: dict, expected_state: Any = None
) -> str:
    """Hash determinístico do plano de uma operação única.

    Vincula capability, parâmetros selados e estado esperado — o mesmo
    critério de imutabilidade do ``plan_hash`` do lote.
    """
    return hashlib.sha256(
        _canonical(
            {
                "capability": capability,
                "params": payload,
                "expected_state": expected_state,
            }
        ).encode()
    ).hexdigest()


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
    """Exige token emitido depois da emissão do desafio.

    Controle secundário de frescor: garante que a sessão que aprovou
    é posterior à existência do objeto de autorização — um token
    emitido antes do PREPARE/desafio não pode autorizá-lo. A prova
    primária de consentimento é o desafio APPROVED vinculado ao plano.
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


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _challenge_view(challenge: dict | None) -> dict | None:
    if challenge is None:
        return None
    return {
        "challenge_id": str(challenge["challenge_id"]),
        "status": challenge["status"],
        "created_at": _iso(challenge["created_at"]),
        "approved_at": _iso(challenge["approved_at"]),
        "expires_at": _iso(challenge["expires_at"]),
    }


class ClaraStepUpConsent:
    """Consentimento por superfície confiável (desafio + token fresco)."""

    def __init__(
        self,
        *,
        batches: ClaraBatchRepository | None = None,
        proposals: ClaraProposalRepository | None = None,
        challenges: ClaraConsentChallengeRepository | None = None,
    ) -> None:
        self._batches = batches or ClaraBatchRepository()
        self._proposals = proposals or ClaraProposalRepository()
        self._challenges = challenges or ClaraConsentChallengeRepository()

    # -- emissão de desafio (PREPARE) -----------------------------------

    def issue_batch_challenge(
        self,
        *,
        batch_id: str,
        actor_sub: str,
        plan_hash: str,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict:
        return self._challenges.issue_for_batch(
            batch_id=batch_id,
            actor_sub=actor_sub,
            plan_hash=plan_hash,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )

    def issue_proposal_challenge(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        capability: str,
        payload: dict,
        expected_state: Any,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict:
        return self._challenges.issue_for_proposal(
            proposal_id=proposal_id,
            actor_sub=actor_sub,
            plan_hash=proposal_plan_hash(
                capability, payload, expected_state
            ),
            expires_at=expires_at,
            correlation_id=correlation_id,
        )

    # -- batch ----------------------------------------------------------

    def _batch_challenge(self, batch: dict) -> dict | None:
        challenge = self._challenges.latest_for_batch(
            batch_id=str(batch["batch_id"])
        )
        if challenge is None and batch["status"] == "PREPARED":
            # Lote PREPARED sem desafio (legado/falha de emissão):
            # emite sob demanda — mesmo vínculo de ator+plano.
            challenge = self._challenges.issue_for_batch(
                batch_id=str(batch["batch_id"]),
                actor_sub=batch["actor_sub"],
                plan_hash=batch["plan_hash"],
                expires_at=batch["expires_at"],
                correlation_id=batch.get("correlation_id"),
            )
        return challenge

    def batch_summary(self, *, batch_id: str, actor_sub: str) -> dict:
        """Plano selado completo para a superfície de consentimento."""
        batch = self._batches.get_batch(batch_id=batch_id)
        if batch["actor_sub"] != actor_sub:
            raise BatchActorMismatch("Lote pertence a outro ator.")
        plan = batch.get("plan") or {}
        if isinstance(plan, str):
            plan = json.loads(plan)
        op_rows = {
            int(op["seq"]): op
            for op in batch.get("operations", [])
        }
        operations: list[dict] = []
        periods: list[str] = []
        blocked = executable = dependent = 0
        all_displayable = True
        for op in plan.get("operations", []):
            index = int(op["index"])
            viable = op.get("status") == "viable"
            presentation = op.get("presentation")
            if not isinstance(presentation, dict) or not presentation.get(
                "summary"
            ):
                presentation = present_operation(
                    op["capability"], op.get("params") or {}
                )
            period = (op.get("params") or {}).get("period")
            if period:
                periods.append(str(period))
            row = op_rows.get(index)
            state = row["state"] if row else (
                "BLOCKED" if not viable else "PREPARED"
            )
            if viable:
                executable += 1
                if not presentation.get("displayable"):
                    all_displayable = False
            else:
                blocked += 1
            depends_on = [int(d) for d in (op.get("depends_on") or [])]
            if depends_on:
                dependent += 1
            block_reason = op.get("block_reason")
            operations.append(
                {
                    "index": index,
                    "seq": index,
                    "capability": op["capability"],
                    "viability": "executable" if viable else "blocked",
                    "state": state,
                    "presentation": presentation,
                    "resource_type": op.get("resource_type"),
                    "resource_key": op.get("resource_key"),
                    "period": period,
                    "depends_on": depends_on,
                    "block_reason": block_reason,
                    "block_message": (
                        _BLOCK_REASON_PT.get(
                            block_reason,
                            "Operação bloqueada na análise do pedido.",
                        )
                        if block_reason
                        else None
                    ),
                    "missing_params": op.get("missing_params") or [],
                }
            )
        expired = _epoch(batch["expires_at"]) < (
            datetime.now(timezone.utc).timestamp()
        )
        consentable = (
            batch["status"] == "PREPARED"
            and not expired
            and executable > 0
            and all_displayable
        )
        if not all_displayable:
            consent_block_reason = "operation_not_displayable"
        elif batch["status"] != "PREPARED":
            consent_block_reason = "not_prepared"
        elif expired:
            consent_block_reason = "expired"
        elif executable == 0:
            consent_block_reason = "no_executable_operations"
        else:
            consent_block_reason = None
        return {
            "batch_id": batch_id,
            "status": batch["status"],
            "plan_hash": batch["plan_hash"],
            "consent_mode": batch["consent_mode"],
            "actor_sub": batch["actor_sub"],
            "correlation_id": batch.get("correlation_id"),
            "expires_at": _iso(batch["expires_at"]),
            "created_at": _iso(batch["created_at"]),
            "confirmed_at": _iso(batch.get("confirmed_at")),
            "challenge": _challenge_view(self._batch_challenge(batch)),
            "competence": {
                "period": periods[0] if periods else None,
                "period_label": (
                    period_label(periods[0]) if periods else None
                ),
            },
            "totals": {
                "total": len(operations),
                "executable": executable,
                "blocked": blocked,
                "dependent": dependent,
            },
            "consentable": consentable,
            "consent_block_reason": consent_block_reason,
            "operations": operations,
        }

    def record_batch_consent(
        self,
        *,
        batch_id: str,
        actor_sub: str,
        token_claims: dict,
        challenge_id: str | None,
    ) -> dict:
        batch = self._batches.get_batch(batch_id=batch_id)
        if batch["actor_sub"] != actor_sub:
            raise BatchActorMismatch("Lote pertence a outro ator.")
        if batch["status"] == "CONFIRMED":
            # Duplo clique honesto: mesmo desafio + mesmo ator ⇒
            # devolve o estado vigente, nunca um segundo registro.
            existing = batch.get("consent_record") or {}
            if isinstance(existing, str):
                existing = json.loads(existing)
            if (
                challenge_id
                and existing.get("challenge_id") == str(challenge_id)
                and existing.get("confirmed_by") == actor_sub
            ):
                return {
                    "batch_id": batch_id,
                    "status": "CONFIRMED",
                    "consent_mode": "CONSOLIDATED",
                    "challenge_id": str(challenge_id),
                    "confirmed_at": _iso(batch.get("confirmed_at")),
                }
            raise BatchNotConfirmed(
                "Lote já confirmado por outra autorização."
            )
        if batch["status"] != "PREPARED":
            raise BatchNotConfirmed(
                f"Lote em estado {batch['status']} — não aceita "
                "consentimento."
            )
        expires = _epoch(batch["expires_at"])
        if expires < datetime.now(timezone.utc).timestamp():
            raise ConsentRequired("Lote expirado — reprepare o plano.")
        if not challenge_id:
            raise ConsentChallengeRequired(
                "Identificador do desafio de consentimento ausente."
            )
        challenge = self._challenges.get_by_id(
            challenge_id=str(challenge_id)
        )
        # O token deve ser emitido DEPOIS da emissão do desafio —
        # credencial que o canal MCP não consegue produzir.
        proof = assert_step_up_token(
            token_claims, prepared_at=challenge["created_at"]
        )
        self._assert_batch_displayable(batch)
        consent_record = {
            "type": CONSENT_TYPE_PORTAL_STEP_UP,
            "confirmed_by": actor_sub,
            "plan_hash": batch["plan_hash"],
            "plan_version": 1,
            "challenge_id": str(challenge["challenge_id"]),
            "origin": "portal",
            "correlation_id": challenge.get("correlation_id"),
            "approved_at": _now_iso(),
            "expires_at": _iso(batch["expires_at"]),
            "recorded_at": _now_iso(),
            **proof,
        }
        updated = self._challenges.approve_for_batch(
            challenge_id=str(challenge_id),
            batch_id=batch_id,
            actor_sub=actor_sub,
            plan_hash=batch["plan_hash"],
            consent_record=consent_record,
            token_jti=proof.get("token_jti"),
            token_iat=(
                datetime.fromtimestamp(
                    float(proof["token_iat"]), tz=timezone.utc
                )
            ),
        )
        return {
            "batch_id": batch_id,
            "status": updated["status"],
            "consent_mode": "CONSOLIDATED",
            "challenge_id": str(challenge["challenge_id"]),
            "confirmed_at": _iso(updated["confirmed_at"]),
        }

    def _assert_batch_displayable(self, batch: dict) -> None:
        """Toda operação executável precisa ser representável."""
        plan = batch.get("plan") or {}
        if isinstance(plan, str):
            plan = json.loads(plan)
        for op in plan.get("operations", []):
            if op.get("status") != "viable":
                continue
            presentation = op.get("presentation")
            if isinstance(presentation, dict) and presentation.get(
                "displayable"
            ):
                continue
            recomputed = present_operation(
                op["capability"], op.get("params") or {}
            )
            if not recomputed.get("displayable"):
                raise ConsentNotDisplayable(
                    "Há operação sem representação clara — o plano "
                    "não pode ser autorizado sem que o usuário saiba "
                    "exatamente o que está aprovando."
                )

    # -- proposal --------------------------------------------------------

    def _proposal_challenge(self, proposal: dict) -> dict | None:
        challenge = self._challenges.latest_for_proposal(
            proposal_id=str(proposal["proposal_id"])
        )
        if (
            challenge is None
            and proposal.get("consented_at") is None
            and proposal.get("batch_operation_id") is None
        ):
            challenge = self._challenges.issue_for_proposal(
                proposal_id=str(proposal["proposal_id"]),
                actor_sub=proposal["actor_sub"],
                plan_hash=proposal_plan_hash(
                    proposal["capability"],
                    proposal["payload"],
                    proposal["expected_state"],
                ),
                expires_at=proposal["expires_at"],
            )
        return challenge

    def proposal_summary(self, *, proposal_id: str,
                         actor_sub: str) -> dict:
        proposal = self._proposals.get_by_id(proposal_id=proposal_id)
        if proposal["actor_sub"] != actor_sub:
            raise ProposalActorMismatch(
                "Proposta pertence a outro ator."
            )
        payload = proposal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        presentation = present_operation(
            proposal["capability"], payload
        )
        expired = _epoch(proposal["expires_at"]) < (
            datetime.now(timezone.utc).timestamp()
        )
        batch_owned = proposal.get("batch_operation_id") is not None
        consentable = (
            not batch_owned
            and not expired
            and proposal["execution_state"] == "PREPARED"
            and presentation.get("displayable", False)
        )
        if batch_owned:
            consent_block_reason = "batch_owned"
        elif expired:
            consent_block_reason = "expired"
        elif proposal["execution_state"] != "PREPARED":
            consent_block_reason = "not_prepared"
        elif not presentation.get("displayable"):
            consent_block_reason = "operation_not_displayable"
        else:
            consent_block_reason = None
        return {
            "proposal_id": proposal_id,
            "capability": proposal["capability"],
            "resource_type": proposal["resource_type"],
            "resource_key": proposal["resource_key"],
            "params": payload,
            "presentation": presentation,
            "expected_state": proposal["expected_state"],
            "execution_state": proposal["execution_state"],
            "consented_at": _iso(proposal.get("consented_at")),
            "expires_at": _iso(proposal["expires_at"]),
            "created_at": _iso(proposal["created_at"]),
            "challenge": _challenge_view(
                self._proposal_challenge(proposal)
            ),
            "period": payload.get("period"),
            "period_label": period_label(payload.get("period")),
            "consentable": consentable,
            "consent_block_reason": consent_block_reason,
        }

    def record_proposal_consent(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        token_claims: dict,
        challenge_id: str | None,
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
        if proposal.get("consented_at") is not None:
            existing = proposal.get("consent_record") or {}
            if isinstance(existing, str):
                existing = json.loads(existing)
            if (
                challenge_id
                and existing.get("challenge_id") == str(challenge_id)
                and existing.get("confirmed_by") == actor_sub
            ):
                return {
                    "proposal_id": proposal_id,
                    "consented_at": _iso(proposal["consented_at"]),
                }
            raise ConsentRequired(
                "Proposta já consentida por outra autorização."
            )
        if proposal["execution_state"] != "PREPARED":
            raise ConsentRequired(
                "Proposta já em execução ou encerrada — reprepare "
                "a operação."
            )
        expires = _epoch(proposal["expires_at"])
        if expires < datetime.now(timezone.utc).timestamp():
            raise ConsentRequired(
                "Proposta expirada — reprepare a operação."
            )
        if not challenge_id:
            raise ConsentChallengeRequired(
                "Identificador do desafio de consentimento ausente."
            )
        challenge = self._challenges.get_by_id(
            challenge_id=str(challenge_id)
        )
        proof = assert_step_up_token(
            token_claims, prepared_at=challenge["created_at"]
        )
        payload = proposal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not present_operation(
            proposal["capability"], payload
        ).get("displayable"):
            raise ConsentNotDisplayable(
                "Operação sem representação clara — não autorizável."
            )
        plan_hash = proposal_plan_hash(
            proposal["capability"], payload, proposal["expected_state"]
        )
        consent_record = {
            "type": CONSENT_TYPE_PORTAL_STEP_UP,
            "confirmed_by": actor_sub,
            "capability": proposal["capability"],
            "resource_key": proposal["resource_key"],
            "plan_hash": plan_hash,
            "plan_version": 1,
            "challenge_id": str(challenge["challenge_id"]),
            "origin": "portal",
            "correlation_id": challenge.get("correlation_id"),
            "approved_at": _now_iso(),
            "expires_at": _iso(proposal["expires_at"]),
            "recorded_at": _now_iso(),
            **proof,
        }
        updated = self._challenges.approve_for_proposal(
            challenge_id=str(challenge_id),
            proposal_id=proposal_id,
            actor_sub=actor_sub,
            plan_hash=plan_hash,
            consent_record=consent_record,
            token_jti=proof.get("token_jti"),
            token_iat=(
                datetime.fromtimestamp(
                    float(proof["token_iat"]), tz=timezone.utc
                )
            ),
        )
        return {
            "proposal_id": proposal_id,
            "consented_at": _iso(updated["consented_at"]),
        }
