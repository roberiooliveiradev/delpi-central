"""DAVI governed write orchestrator — PREPARE / ACT for the execute tool.

PREPARE validates intent, reads authoritative owner state, seals a
server-side proposal bound to the caller and returns a confirmation
summary. ACT accepts only the proposal reference + explicit confirmation,
revalidates identity/authorization/state and executes the sealed change
through the owner API — the model can never reconstruct the payload.
"""

from __future__ import annotations

import logging
from typing import Any

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.external_capabilities.governed_writes.errors import (
    CAPABILITY_NOT_ALLOWED,
    CONFIRMATION_REQUIRED,
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_STALE,
    UNAUTHENTICATED,
    UNKNOWN_RESULT,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.proposal import (
    create_proposal,
)
from app.application.external_capabilities.governed_writes.proposal_store import (
    get_proposal_store,
    parse_proposal_handle,
    resolve_proposal_handle,
)
from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    SI_GOAL_WRITE_CAPABILITIES,
    SiGoalWriteStack,
    owner_error_to_governed,
)

logger = logging.getLogger(__name__)

# Authoritative reconciliation procedure returned on ambiguous outcomes.
# The consumed proposal can never be re-executed; the caller must read the
# owner state and only PREPARE again if the mutation is provably absent.
_RECONCILIATION_HINT = (
    "Read the authoritative state via the read tool "
    "(list_si_indicator_goals / list_si_indicator_goal_history); the "
    "consumed proposal cannot be re-executed. PREPARE a new proposal "
    "only if reconciliation proves the mutation did not take effect."
)

# All approved capabilities require the two-step confirmation flow.
WRITE_CAPABILITIES = SI_GOAL_WRITE_CAPABILITIES


def _require_identity(actor_id: str | None, authorization: str | None) -> str:
    if not actor_id or not (authorization or "").strip():
        raise GovernedWriteError(
            "Authentication required.",
            code=UNAUTHENTICATED,
            status_code=401,
        )
    return authorization.strip()


class DaviGovernedWriteOrchestrator:
    def __init__(self, si_stack: SiGoalWriteStack | None = None) -> None:
        self._si_stack = si_stack or SiGoalWriteStack()

    # ------------------------------------------------------------- PREPARE

    def prepare(
        self,
        *,
        capability: str,
        args: dict[str, Any] | None,
        actor_id: str | None,
        actor_email: str | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        if capability not in WRITE_CAPABILITIES:
            raise GovernedWriteError(
                f"Capability '{capability}' is not an approved governed write.",
                code=CAPABILITY_NOT_ALLOWED,
                status_code=400,
            )
        token = _require_identity(actor_id, authorization)

        try:
            prepared = self._si_stack.prepare(token, capability, dict(args or {}))
        except StrategicIndicatorsApiError as exc:
            raise owner_error_to_governed(exc) from exc
        proposal = create_proposal(
            capability=capability,
            actor_id=actor_id,
            actor_email=actor_email,
            resource_type=prepared["resource_type"],
            resource_id=prepared.get("resource_id"),
            current_state_fingerprint=prepared["current_state_fingerprint"],
            exact_change=prepared["exact_change"],
            validation_result=prepared["validation_result"],
            consequential_impact=prepared["consequential_impact"],
            confirmation_requirement=prepared["confirmation_requirement"],
            expected_postcondition=prepared["expected_postcondition"],
            execution_policy="confirm_before_act",
        )
        handle = get_proposal_store().put(proposal)
        logger.info(
            "governed_write_prepare_sealed correlation_id=%s capability=%s "
            "proposal_id=%s actor_id=%s resource_type=%s expires_at=%s",
            proposal.proposal_id,
            capability,
            proposal.proposal_id,
            proposal.actor_id,
            proposal.resource_type,
            int(proposal.expires_at),
        )
        public = proposal.to_public_dict()
        public["phase"] = "prepare"
        public["proposal_handle"] = handle
        public["ready"] = bool(prepared["validation_result"].get("ready", True))
        public["act_allowed"] = public["ready"]
        return public

    # ----------------------------------------------------------------- ACT

    def act(
        self,
        *,
        capability: str,
        proposal_handle: str | None,
        proposal_id: str | None,
        confirm: bool | None,
        actor_id: str | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        if capability not in WRITE_CAPABILITIES:
            raise GovernedWriteError(
                f"Capability '{capability}' is not an approved governed write.",
                code=CAPABILITY_NOT_ALLOWED,
                status_code=400,
            )
        token = _require_identity(actor_id, authorization)
        if confirm is not True:
            raise GovernedWriteError(
                "ACT requires confirm=true (explicit human confirmation).",
                code=CONFIRMATION_REQUIRED,
                status_code=400,
            )
        handle = resolve_proposal_handle(
            proposal_handle=proposal_handle, proposal_id=proposal_id
        )
        # Atomic validate+consume under one critical section: closes the
        # check→consume race — two concurrent ACTs on the same proposal can
        # never both pass validation.
        proposal = get_proposal_store().take_for_act(
            parse_proposal_handle(handle),
            actor_id=actor_id,
            expected_capability=capability,
        )
        if not proposal.validation_result.get("ready", True):
            raise GovernedWriteError(
                "Proposal is not ready for ACT (validation failed).",
                code=PROPOSAL_STALE,
                status_code=409,
            )

        # Re-read owner state and re-verify the sealed fingerprint. Owner
        # errors here (e.g. revoked permission) map to the same typed
        # contract as the write path — ACT revalidates authorization.
        try:
            current_fp = self._si_stack.recompute_fingerprint(
                token, capability, proposal.exact_change
            )
        except StrategicIndicatorsApiError as exc:
            raise owner_error_to_governed(exc) from exc
        if current_fp != proposal.current_state_fingerprint:
            raise GovernedWriteError(
                "Current state changed since PREPARE. Prepare again.",
                code=PROPOSAL_STALE,
                status_code=409,
                data={
                    "expected_fingerprint": proposal.current_state_fingerprint,
                    "actual_fingerprint": current_fp,
                },
            )

        # Single-use: the proposal was consumed atomically at validation —
        # an ambiguous transport failure can never silently re-execute. The
        # owner-side optimistic precondition (sealed into exact_change) is
        # still enforced atomically by the SI API inside the mutation.
        try:
            write_result = self._si_stack.execute(
                token,
                capability,
                proposal.exact_change,
                correlation_id=proposal.proposal_id,
            )
        except StrategicIndicatorsApiError as exc:
            governed = owner_error_to_governed(exc)
            logger.warning(
                "governed_write_act_rejected correlation_id=%s capability=%s "
                "proposal_id=%s actor_id=%s code=%s owner_status=%s",
                proposal.proposal_id,
                capability,
                proposal.proposal_id,
                proposal.actor_id,
                governed.code,
                exc.status_code,
            )
            raise governed from exc

        # Authoritative read-back / postcondition verification.
        try:
            verified = self._si_stack.verify(
                token,
                capability,
                proposal.exact_change,
                proposal.expected_postcondition,
                write_result,
            )
        except GovernedWriteError:
            raise
        except StrategicIndicatorsApiError as exc:
            logger.exception(
                "governed_write_verify_transport_failed correlation_id=%s "
                "capability=%s proposal_id=%s actor_id=%s",
                proposal.proposal_id,
                capability,
                proposal.proposal_id,
                proposal.actor_id,
            )
            raise GovernedWriteError(
                "Write may have occurred but the outcome could not be "
                "verified. Do not retry blindly; read the current state first.",
                code=UNKNOWN_RESULT,
                status_code=409,
                data={
                    "capability": capability,
                    "proposal_id": proposal.proposal_id,
"reconciliation": _RECONCILIATION_HINT,
                },
            ) from exc
        except Exception as exc:
            logger.exception(
                "governed_write_verify_failed correlation_id=%s "
                "capability=%s proposal_id=%s actor_id=%s",
                proposal.proposal_id,
                capability,
                proposal.proposal_id,
                proposal.actor_id,
            )
            raise GovernedWriteError(
                "Write may have occurred but the outcome could not be "
                "verified. Do not retry blindly; read the current state first.",
                code=OUTCOME_VERIFICATION_FAILED,
                status_code=409,
                data={
                    "capability": capability,
                    "proposal_id": proposal.proposal_id,
"reconciliation": _RECONCILIATION_HINT,
                },
            ) from exc

        logger.info(
            "governed_write_act_verified correlation_id=%s capability=%s "
            "proposal_id=%s actor_id=%s resource_type=%s resource_id=%s",
            proposal.proposal_id,
            capability,
            proposal.proposal_id,
            proposal.actor_id,
            proposal.resource_type,
            proposal.resource_id,
        )
        return {
            "phase": "act",
            "verified": True,
            "capability": capability,
            "proposal_id": proposal.proposal_id,
            "data": verified,
        }


_orchestrator: DaviGovernedWriteOrchestrator | None = None


def get_davi_write_orchestrator() -> DaviGovernedWriteOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DaviGovernedWriteOrchestrator()
    return _orchestrator


def davi_execute(
    *,
    capability: str,
    arguments: dict[str, Any] | None = None,
    proposal_handle: str | None = None,
    proposal_id: str | None = None,
    confirm: bool | None = None,
    actor_id: str | None,
    actor_email: str | None = None,
    authorization: str | None,
    orchestrator: DaviGovernedWriteOrchestrator | None = None,
) -> dict[str, Any]:
    """Execute-tool entry: PREPARE (no proposal ref) or ACT (proposal ref)."""
    orchestrator = orchestrator or get_davi_write_orchestrator()
    if proposal_handle or proposal_id:
        return orchestrator.act(
            capability=capability,
            proposal_handle=proposal_handle,
            proposal_id=proposal_id,
            confirm=confirm,
            actor_id=actor_id,
            authorization=authorization,
        )
    return orchestrator.prepare(
        capability=capability,
        args=arguments,
        actor_id=actor_id,
        actor_email=actor_email,
        authorization=authorization,
    )
