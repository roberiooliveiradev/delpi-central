"""Governed-write deterministic rules — provider-neutral.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): the
static write-binding registry (``GOVERNED_WRITE_BINDINGS`` /
``write_binding_for`` / ``GovernedWriteBinding``) is superseded — the
specialist owns capability existence and pairing, advertised live via
``tools/list``. These rules only project owner payloads, bind exact
confirmations, decide continuation and project outcomes against the
live capability reference — no capability availability lookup exists
here or anywhere else in DÉLIA.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from app.domain.governed_write.model import (
    ConfirmationDecision,
    ConfirmationReason,
    ConfirmationRecord,
    ConfirmationState,
    ProposalReadiness,
    StructuredConfirmation,
    WriteGateDecision,
    WriteGateReason,
    WriteGateStatus,
    WriteOutcomeProjection,
    WriteOutcomeStatus,
    WriteProposalPreview,
)


def proposal_digest(proposal_ref: str) -> str:
    """Non-reversible bounded reference for correlation/audit.

    The raw owner proposal handle is never logged or persisted by DÉLIA;
    this digest is correlation identity only, never authority.
    """
    return hashlib.sha256(str(proposal_ref).encode("utf-8")).hexdigest()


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    except (TypeError, ValueError):
        return repr(value)


def preview_fingerprint(preview: WriteProposalPreview) -> str:
    """Deterministic DÉLIA-side fingerprint of the bounded preview.

    Correlation identity for confirmation binding only — it never
    replaces or reinterprets the owner's business state fingerprint.
    """
    canonical = {
        "capability_ref": preview.capability_ref,
        "owner_capability": preview.owner_capability,
        "proposal_digest": proposal_digest(preview.proposal_ref),
        "resource_ref": preview.resource_ref,
        "exact_change": preview.exact_change,
        "expected_postcondition": preview.expected_postcondition,
        "expires_at_epoch": preview.expires_at_epoch,
        "readiness": preview.readiness.value,
    }
    return hashlib.sha256(_canonical(canonical).encode("utf-8")).hexdigest()


def _proposal_container(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Locate the owner proposal object — generic envelope handling.

    Owners may project governance fields flat on the data payload or
    nested under a declared ``proposal`` object; both shapes carry the
    same contract. Absent envelope, the payload is the container.
    """
    proposal = payload.get("proposal")
    if isinstance(proposal, Mapping):
        return proposal
    return payload


def _readiness_for(payload: Mapping[str, Any], now_epoch: float) -> ProposalReadiness:
    """Classify owner PREPARE payload readiness — fail closed.

    Mandatory governance fields for a safe confirmation: an opaque
    proposal reference and a bounded exact-change preview. Missing or
    malformed mandatory fields -> INVALID, never inferred READY.
    """
    container = _proposal_container(payload)
    proposal_ref = str(
        container.get("proposal_handle") or container.get("handle") or ""
    ).strip()
    exact_change = container.get("exact_change")
    if not proposal_ref or not isinstance(exact_change, Mapping):
        return ProposalReadiness.INVALID
    expires_at = container.get("expires_at")
    try:
        expires = float(expires_at) if expires_at is not None else None
    except (TypeError, ValueError):
        return ProposalReadiness.INVALID
    if expires is not None and expires <= now_epoch:
        return ProposalReadiness.EXPIRED
    ready = container.get("ready")
    validation = container.get("validation_result")
    if not isinstance(validation, Mapping):
        validation = payload.get("validation_result")
    if isinstance(validation, Mapping) and validation.get("ready") is False:
        return ProposalReadiness.NOT_READY
    if ready is True or (
        ready is None
        and isinstance(validation, Mapping)
        and validation.get("ready") is True
    ):
        return ProposalReadiness.READY
    if ready is False:
        return ProposalReadiness.NOT_READY
    return ProposalReadiness.UNKNOWN


def project_proposal_preview(
    *,
    capability_ref: str,
    remote_capability: str,
    owner_payload: Mapping[str, Any],
    specialist_id: str,
    correlation_id: str,
    observed_at: str,
    now_epoch: float,
    limitations: tuple[str, ...] = (),
) -> WriteProposalPreview:
    """Normalize an owner PREPARE result into a bounded preview.

    The payload is untrusted owner data: only the declared governance
    fields are projected; anything else is dropped. The preview never
    authorizes ACT.
    """
    data = owner_payload.get("data")
    inner = data if isinstance(data, Mapping) else owner_payload
    container = _proposal_container(inner)
    readiness = _readiness_for(inner, now_epoch)

    def _governance_field(name: str) -> Any:
        """Envelope-first lookup — governance fields may live inside the
        declared ``proposal`` object or flat on the data payload."""
        value = container.get(name)
        if value is None and container is not inner:
            value = inner.get(name)
        return value

    expires_raw = _governance_field("expires_at")
    try:
        expires = float(expires_raw) if expires_raw is not None else None
    except (TypeError, ValueError):
        expires = None
    proposal_ref = str(
        container.get("proposal_handle") or container.get("handle") or ""
    ).strip()
    exact_change = _governance_field("exact_change")
    validation_result = _governance_field("validation_result")
    resource_id = _governance_field("resource_id")
    impact = _governance_field("consequential_impact")
    confirmation_req = _governance_field("confirmation_requirement")
    if not isinstance(confirmation_req, Mapping):
        confirmation_req = _governance_field("confirmationPolicy")
    postcondition = _governance_field("expected_postcondition")
    return WriteProposalPreview(
        capability_ref=capability_ref,
        owner_capability=str(
            _governance_field("capability") or remote_capability
        ).strip(),
        proposal_ref=proposal_ref,
        readiness=readiness,
        specialist_id=specialist_id,
        correlation_id=correlation_id,
        observed_at=observed_at,
        resource_ref=(
            str(resource_id).strip() if resource_id is not None else None
        ),
        exact_change=(
            exact_change if isinstance(exact_change, Mapping) else None
        ),
        validation_summary=(
            validation_result
            if isinstance(validation_result, Mapping)
            else None
        ),
        consequential_impact=(
            impact if isinstance(impact, Mapping) else None
        ),
        confirmation_requirement=(
            confirmation_req
            if isinstance(confirmation_req, Mapping)
            else None
        ),
        expected_postcondition=(
            postcondition if isinstance(postcondition, Mapping) else None
        ),
        expires_at_epoch=expires,
        limitations=limitations,
    )


def bind_confirmation(
    *,
    preview: WriteProposalPreview,
    confirmation: StructuredConfirmation,
    expected_actor_id: str,
    expected_session_id: str,
    now_epoch: float,
) -> ConfirmationRecord:
    """Bind a structured confirmation to the exact preview, fail closed.

    Every identity dimension must match deterministically; any mismatch
    or staleness yields INVALIDATED/EXPIRED/REJECTED — never CONFIRMED.
    CONFIRMED still authorizes nothing (confirmation != authorization).
    """
    reasons: list[ConfirmationReason] = []
    if confirmation.actor_user_id != expected_actor_id:
        reasons.append(ConfirmationReason.ACTOR_MISMATCH)
    if confirmation.session_id != expected_session_id:
        reasons.append(ConfirmationReason.SESSION_MISMATCH)
    if confirmation.capability_ref != preview.capability_ref:
        reasons.append(ConfirmationReason.BINDING_MISMATCH)
    if confirmation.proposal_digest != proposal_digest(preview.proposal_ref):
        reasons.append(ConfirmationReason.PROPOSAL_MISMATCH)
    if confirmation.preview_fingerprint != preview_fingerprint(preview):
        reasons.append(ConfirmationReason.PREVIEW_CHANGED)
    if preview.expires_at_epoch is not None and (
        preview.expires_at_epoch <= now_epoch
    ):
        reasons.append(ConfirmationReason.PROPOSAL_EXPIRED)
    if preview.readiness is not ProposalReadiness.READY:
        reasons.append(ConfirmationReason.PROPOSAL_NOT_READY)

    if reasons:
        state = (
            ConfirmationState.EXPIRED
            if ConfirmationReason.PROPOSAL_EXPIRED in reasons
            and len(reasons) == 1
            else ConfirmationState.INVALIDATED
        )
        return ConfirmationRecord(
            state=state, reason_codes=tuple(reasons), confirmation=confirmation
        )
    if confirmation.decision is ConfirmationDecision.REJECT:
        return ConfirmationRecord(
            state=ConfirmationState.REJECTED,
            reason_codes=(ConfirmationReason.USER_REJECTED,),
            confirmation=confirmation,
        )
    return ConfirmationRecord(
        state=ConfirmationState.CONFIRMED,
        reason_codes=(ConfirmationReason.EXACT_PREVIEW_CONFIRMED,),
        confirmation=confirmation,
    )


def evaluate_write_continuation(
    *,
    capability_live: bool,
    confirmation_required: bool,
    preview: WriteProposalPreview | None,
    confirmation: ConfirmationRecord | None,
    now_epoch: float,
) -> WriteGateDecision:
    """Decide whether a governed write may continue toward an ACT call.

    Fail-closed ordering: capability absent from the fresh live surface
    -> not-ready or expired preview -> missing/mismatched/rejected
    confirmation -> READY_FOR_LIVE_REVALIDATION at most. No state here
    authorizes ACT.
    """
    capability_ref = preview.capability_ref if preview is not None else None
    if not capability_live:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.CAPABILITY_NOT_LIVE,),
            capability_ref=capability_ref,
        )
    if preview is None or preview.readiness is ProposalReadiness.INVALID:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_NOT_READY,),
            capability_ref=capability_ref,
        )
    if preview.readiness is ProposalReadiness.EXPIRED or (
        preview.expires_at_epoch is not None
        and preview.expires_at_epoch <= now_epoch
    ):
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_EXPIRED,),
            capability_ref=capability_ref,
        )
    if preview.readiness is not ProposalReadiness.READY:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_NOT_READY,),
            capability_ref=capability_ref,
        )
    if confirmation_required and confirmation is None:
        return WriteGateDecision(
            status=WriteGateStatus.REQUIRES_CONFIRMATION,
            reason_codes=(WriteGateReason.CONFIRMATION_MISSING,),
            capability_ref=capability_ref,
        )
    if confirmation is not None:
        if confirmation.state is ConfirmationState.REJECTED:
            return WriteGateDecision(
                status=WriteGateStatus.REJECTED,
                reason_codes=(WriteGateReason.USER_REJECTED,),
                capability_ref=capability_ref,
            )
        if confirmation.state is not ConfirmationState.CONFIRMED:
            return WriteGateDecision(
                status=WriteGateStatus.BLOCKED,
                reason_codes=(WriteGateReason.CONFIRMATION_MISMATCH,),
                capability_ref=capability_ref,
            )
    # Strongest state: the write may continue only to the ACT boundary
    # where live Core AuthZ + Domain revalidation MUST occur. This is
    # never ACT_AUTHORIZED.
    return WriteGateDecision(
        status=WriteGateStatus.READY_FOR_LIVE_REVALIDATION,
        reason_codes=(
            WriteGateReason.LIVE_AUTHZ_REQUIRED,
            WriteGateReason.DOMAIN_REVALIDATION_REQUIRED,
        ),
        capability_ref=capability_ref,
        live_core_authz_required=True,
        domain_revalidation_required=True,
    )


def project_write_outcome(
    *,
    capability_ref: str,
    remote_capability: str,
    owner_payload: Mapping[str, Any],
    specialist_id: str,
    correlation_id: str,
    occurred_at: str,
    limitations: tuple[str, ...] = (),
) -> WriteOutcomeProjection:
    """Project an owner ACT result into the bounded outcome.

    Technical/transport success is never VERIFIED: only an explicit
    owner-authoritative ``verified`` postcondition evidence projects
    VERIFIED. Unknown shapes fail safe to UNKNOWN/FAILED, never success.
    """
    data = owner_payload.get("data")
    inner = data if isinstance(data, Mapping) else owner_payload
    success = inner.get("success")
    verified = inner.get("verified")

    if success is False:
        status = WriteOutcomeStatus.FAILED
    elif verified is True:
        status = WriteOutcomeStatus.VERIFIED
    elif verified is False:
        status = WriteOutcomeStatus.OUTCOME_VERIFICATION_FAILED
    elif success is True:
        status = WriteOutcomeStatus.EXECUTION_REPORTED
    else:
        status = WriteOutcomeStatus.UNKNOWN

    postcondition = inner.get("postcondition")
    if not isinstance(postcondition, Mapping):
        postcondition = inner.get("verified_payload")
    return WriteOutcomeProjection(
        status=status,
        capability_ref=capability_ref,
        specialist_id=specialist_id,
        owner_capability=str(
            inner.get("capability") or remote_capability
        ).strip(),
        correlation_id=correlation_id,
        occurred_at=occurred_at,
        verified=bool(verified is True),
        postcondition_summary=(
            postcondition if isinstance(postcondition, Mapping) else None
        ),
        limitations=limitations,
    )
