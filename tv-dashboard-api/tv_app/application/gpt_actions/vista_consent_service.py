"""VISTA consent challenge service (SEMANTIC_TOOLS_V1, D-5).

Separates the responsibilities the contract requires:

- **Target identity** → ``target_echo`` at commit (anti wrong-object;
  never consent proof).
- **Proposal integrity** → opaque HMAC ``proposal_handle`` + sealed
  ``plan_hash`` (``proposal.content_hash``).
- **Actor binding** → ``actor_sub`` on both challenge and proposal.
- **Authorization** → Core RBAC + ``PlaylistAccessService`` (unchanged).
- **Human consent** → this service: a backend-minted challenge approved
  through a trusted human channel with a token issued *after* the
  challenge (``iat >= created_at``, CLARA step-up pattern, implemented
  locally — no cross-context import of CLARA services).
- **Commit permission** → confirmationPolicy + a valid consent artifact.

Hosts without a trusted approval channel get ``CONFIRMATION_UNAVAILABLE``
— explicit block, never a silent fallback to ``confirmation=true``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal import VistaProposal
from tv_app.application.gpt_actions.proposal_store import get_proposal_store
from tv_app.application.ports import VistaConsentChallengeRepositoryPort

# Clock skew slack Keycloak ↔ PostgreSQL; the iat check is a SECONDARY
# freshness control — the primary proof is the APPROVED challenge bound
# to the sealed plan, not token age.
_STEP_UP_CLOCK_SKEW_SECONDS = 10
_STEP_UP_FUTURE_IAT_TOLERANCE_SECONDS = 60

CONFIRM_OPS_PREFIXES = ("delete_",)


def _err(message: str, *, code: str, status_code: int,
         details: dict | None = None) -> GptActionsError:
    return GptActionsError(
        message, code=code, status_code=status_code, details=details or {}
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


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def assert_step_up_token(claims: dict, *, prepared_at: Any) -> dict:
    """Token must be issued AFTER the challenge (step-up freshness).

    A JWT minted before PREPARE cannot authorize a challenge it never
    saw; the refresh token that mints a new JWT lives in the trusted
    human channel — not in the agent transport.
    """
    iat = claims.get("iat")
    if iat is None:
        raise _err(
            "Token sem iat — consentimento não verificável.",
            code="STEP_UP_TOKEN_STALE",
            status_code=403,
        )
    prepared_epoch = _epoch(prepared_at)
    now_epoch = datetime.now(timezone.utc).timestamp()
    if float(iat) < prepared_epoch - _STEP_UP_CLOCK_SKEW_SECONDS:
        raise _err(
            "Token anterior ao desafio de consentimento — atualize a "
            "sessão no canal confiável e confirme novamente.",
            code="STEP_UP_TOKEN_STALE",
            status_code=403,
        )
    if float(iat) > now_epoch + _STEP_UP_FUTURE_IAT_TOLERANCE_SECONDS:
        raise _err(
            "Token com iat futuro — relógio fora de sincronia.",
            code="STEP_UP_TOKEN_STALE",
            status_code=403,
        )
    return {
        "token_iat": int(float(iat)),
        "token_jti": claims.get("jti"),
        "token_sub": claims.get("sub"),
    }


def confirm_op_names(proposal: VistaProposal) -> list[str]:
    """Sorted distinct names of confirm-policy ops in the sealed plan."""
    exact = proposal.exact_change if isinstance(proposal.exact_change, dict) else {}
    ops = exact.get("ops") if isinstance(exact.get("ops"), list) else []
    names = {
        str(op.get("op")).strip()
        for op in ops
        if isinstance(op, dict)
        and str(op.get("op") or "").strip().startswith(CONFIRM_OPS_PREFIXES)
    }
    if names:
        return sorted(names)
    # Non-destructive confirm ops still require consent when policy=confirm.
    if str(proposal.confirmation_policy) == "confirm":
        return sorted(
            str(op.get("op")).strip()
            for op in ops
            if isinstance(op, dict) and str(op.get("op") or "").strip()
        )
    return []


def _target_ref(proposal: VistaProposal, confirm_ops: list[str]) -> str:
    """Canonical target identity bound into the challenge.

    ``<resource_id>`` of the proposal plus, when the plan names specific
    entities, ``op:id`` pairs — the consent page displays these and the
    commit's ``target_echo`` re-verifies them byte-equal.
    """
    base = str(proposal.resource_id or "playlist_create")
    refs: list[str] = []
    exact = proposal.exact_change if isinstance(proposal.exact_change, dict) else {}
    ops = exact.get("ops") if isinstance(exact.get("ops"), list) else []
    id_keys = ("slideId", "sectionId", "blockId", "modelId", "dataSourceId")
    for op in ops:
        if not isinstance(op, dict):
            continue
        name = str(op.get("op") or "").strip()
        if name not in confirm_ops:
            continue
        for key in id_keys:
            value = op.get(key)
            if value:
                refs.append(f"{name}:{value}")
                break
        else:
            refs.append(name)
    if refs:
        return f"{base}|{','.join(sorted(refs))}"
    return base


def challenge_view(challenge: dict | None) -> dict | None:
    if challenge is None:
        return None
    return {
        "challengeId": str(challenge["challenge_id"]),
        "status": challenge["status"],
        "action": challenge["action"],
        "targetRef": challenge["target_ref"],
        "origin": challenge["origin"],
        "createdAt": _iso(challenge["created_at"]),
        "approvedAt": _iso(challenge["approved_at"]),
        "expiresAt": _iso(challenge["expires_at"]),
    }


class VistaConsentService:
    """Consent foundation — issue, approve (step-up), verify, consume."""

    def __init__(
        self, *, challenges: VistaConsentChallengeRepositoryPort
    ) -> None:
        # ``challenges`` is the consent repository port — composition
        # roots (interface layer) supply the Postgres or in-memory
        # implementation; application layer never imports infrastructure.
        self._challenges = challenges

    # -- issue (PREPARE) ---------------------------------------------------

    def issue_for_proposal(
        self,
        *,
        proposal: VistaProposal,
        actor_sub: str,
        origin: str,
        correlation_id: str | None = None,
    ) -> dict:
        """Mint (or reuse pending) challenge bound to the sealed plan.

        ``plan_hash`` = ``proposal.content_hash`` — actor + resource +
        state + exact change are already sealed there; nothing later can
        substitute ops without a mismatch.
        """
        names = confirm_op_names(proposal)
        action = ",".join(names) if names else proposal.capability
        expires_at = datetime.fromtimestamp(
            float(proposal.expires_at), tz=timezone.utc
        )
        challenge = self._challenges.issue_for_proposal(
            proposal_id=proposal.proposal_id,
            actor_sub=actor_sub,
            plan_hash=proposal.content_hash,
            target_ref=_target_ref(proposal, names),
            action=action,
            origin=origin,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )
        if challenge is None:
            raise _err(
                "Desafio de consentimento indisponível.",
                code="CONFIRMATION_UNAVAILABLE",
                status_code=503,
            )
        return challenge

    # -- trusted-channel reads --------------------------------------------

    def summary_for_consent(
        self, *, proposal_id: str, actor_sub: str
    ) -> dict:
        """Sealed plan view for the human approval surface."""
        proposal = get_proposal_store().get(str(proposal_id))
        if proposal is None:
            raise _err(
                "Proposta não encontrada ou já consumida.",
                code="PROPOSAL_NOT_FOUND",
                status_code=404,
            )
        if str(proposal.actor_id) != str(actor_sub):
            raise _err(
                "Proposta pertence a outro ator.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        challenge = self._challenges.latest_for_proposal(
            proposal_id=proposal.proposal_id
        )
        expired = float(proposal.expires_at) < datetime.now(
            timezone.utc
        ).timestamp()
        return {
            "proposal": proposal.to_public_dict(),
            "confirmOps": confirm_op_names(proposal),
            "consentable": (
                not expired
                and not proposal.consumed
                and challenge is not None
                and challenge["status"] == "PENDING"
            ),
            "consentBlockReason": (
                "expired"
                if expired
                else "consumed"
                if proposal.consumed
                else "no_pending_challenge"
                if challenge is None or challenge["status"] != "PENDING"
                else None
            ),
            "challenge": challenge_view(challenge),
        }

    # -- approve (human channel) -------------------------------------------

    def approve(
        self,
        *,
        challenge_id: str,
        actor_sub: str,
        token_claims: dict,
    ) -> dict:
        """Record human approval — PENDING→APPROVED + consent_record.

        Requires: challenge exists, PENDING, bound to this actor and to a
        live proposal whose plan_hash still seals the same plan, and a
        token issued after the challenge (step-up freshness).
        """
        challenge = self._challenges.get_by_id(challenge_id=str(challenge_id))
        if challenge is None:
            raise _err(
                "Desafio de consentimento não encontrado.",
                code="CONSENT_CHALLENGE_NOT_FOUND",
                status_code=404,
            )
        if challenge["actor_sub"] != actor_sub:
            raise _err(
                "Desafio pertence a outro ator.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        if challenge["status"] != "PENDING":
            raise _err(
                "Desafio já utilizado, expirado ou revogado — reprepare "
                "a autorização.",
                code="CONSENT_CHALLENGE_CONSUMED",
                status_code=409,
            )
        if challenge["expires_at"] < datetime.now(timezone.utc):
            raise _err(
                "Desafio expirado — reprepare o plano.",
                code="CONSENT_CHALLENGE_EXPIRED",
                status_code=409,
            )
        proposal = get_proposal_store().get(challenge["proposal_id"])
        if proposal is None or proposal.consumed:
            raise _err(
                "Proposta do desafio não existe mais — reprepare o plano.",
                code="PROPOSAL_NOT_FOUND",
                status_code=404,
            )
        if str(proposal.actor_id) != str(actor_sub):
            raise _err(
                "Proposta pertence a outro ator.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        if proposal.content_hash != challenge["plan_hash"]:
            raise _err(
                "Desafio não corresponde ao plano selado.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        # Token sub must be the same human the challenge binds to.
        if str(token_claims.get("sub") or "") != str(actor_sub):
            raise _err(
                "Token de outro usuário — consentimento não verificável.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        proof = assert_step_up_token(
            token_claims, prepared_at=challenge["created_at"]
        )
        consent_record = {
            "type": "vista_consent_challenge",
            "confirmed_by": actor_sub,
            "plan_hash": challenge["plan_hash"],
            "challenge_id": str(challenge["challenge_id"]),
            "origin": challenge["origin"],
            "correlation_id": challenge.get("correlation_id"),
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _iso(challenge["expires_at"]),
            **proof,
        }
        updated = self._challenges.approve(
            challenge_id=str(challenge_id),
            actor_sub=actor_sub,
            plan_hash=challenge["plan_hash"],
            token_jti=proof.get("token_jti"),
            token_iat=datetime.fromtimestamp(
                float(proof["token_iat"]), tz=timezone.utc
            ),
            consent_record=consent_record,
        )
        if updated is None:
            raise _err(
                "Desafio não pôde ser aprovado — vínculo ou estado "
                "inválido.",
                code="CONSENT_MISMATCH",
                status_code=409,
            )
        return {
            "challenge": challenge_view(updated),
            "consentArtifact": str(updated["challenge_id"]),
            "consentRecord": consent_record,
        }

    # -- verify + consume (COMMIT) ------------------------------------------

    def verify_for_commit(
        self,
        *,
        proposal: VistaProposal,
        actor_sub: str,
        consent_artifact: str | None,
        required: bool,
    ) -> dict | None:
        """Validate the consent artifact against the sealed plan.

        ``required`` is True for the semantic write verbs (execute/delete)
        — the artifact is mandatory. For legacy ``commit_change`` an
        artifact is optional but, when present, must fully verify (no
        half-trusted artifact). Returns the APPROVED challenge on success.
        """
        artifact = str(consent_artifact or "").strip()
        if not artifact:
            if required:
                raise _err(
                    "consent_artifact é obrigatório para esta operação — "
                    "obtenha aprovação humana no canal confiável.",
                    code="CONFIRMATION_REQUIRED",
                    status_code=400,
                )
            return None
        challenge = self._challenges.get_by_id(challenge_id=artifact)
        if challenge is None:
            raise _err(
                "consent_artifact desconhecido.",
                code="CONSENT_CHALLENGE_NOT_FOUND",
                status_code=404,
            )
        if (
            challenge["proposal_id"] != proposal.proposal_id
            or challenge["actor_sub"] != str(actor_sub)
            or challenge["plan_hash"] != proposal.content_hash
        ):
            raise _err(
                "consent_artifact não vincula ator/proposta/plano.",
                code="CONSENT_MISMATCH",
                status_code=403,
            )
        if challenge["status"] == "PENDING":
            raise _err(
                "Consentimento ainda não aprovado pelo canal confiável.",
                code="CONFIRMATION_REQUIRED",
                status_code=400,
            )
        if challenge["status"] != "APPROVED":
            raise _err(
                "consent_artifact já utilizado, expirado ou revogado.",
                code="CONSENT_CHALLENGE_CONSUMED",
                status_code=409,
            )
        return challenge

    def consume_for_commit(
        self, *, challenge: dict, proposal_id: str, actor_sub: str
    ) -> None:
        """Single-use: the first commit consumes the artifact."""
        consumed = self._challenges.consume_approved(
            challenge_id=str(challenge["challenge_id"]),
            proposal_id=proposal_id,
            actor_sub=actor_sub,
        )
        if consumed is None:
            raise _err(
                "consent_artifact já utilizado por outro commit.",
                code="CONSENT_CHALLENGE_CONSUMED",
                status_code=409,
            )
