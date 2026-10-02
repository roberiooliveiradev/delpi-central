"""C5-GOVERNED-WRITE-FOUNDATION-01 governed-write deterministic rules.

Foundation only: gate semantics, proposal-preview projection and
readiness, deterministic confirmation binding, write-continuation
decision, outcome projection, and digest/redaction helpers. No wire
mechanics — PREPARE/ACT remote execution stays phase-gated elsewhere.
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
    GovernedWriteBinding,
    ProposalReadiness,
    StructuredConfirmation,
    WriteGateDecision,
    WriteGateReason,
    WriteGateStatus,
    WriteOutcomeProjection,
    WriteOutcomeStatus,
    WriteProposalPreview,
)


# C5-GOVERNED-WRITE-FOUNDATION-01: static DÉLIA-owned write bindings.
# EMPTY BY DESIGN — no business binding is enabled in this task. Real
# owner bindings (e.g. TÉO/VISTA PREPARE→ACT pairs) may appear here only
# under an explicit future task authorization; naming a binding grants
# nothing and a listed binding still requires enabled=True.
GOVERNED_WRITE_BINDINGS: dict[str, GovernedWriteBinding] = {}


def write_binding_for(binding_id: str) -> GovernedWriteBinding | None:
    """Return the static binding, or None. Remote metadata is ignored."""
    return GOVERNED_WRITE_BINDINGS.get(str(binding_id or "").strip())


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
        "binding_id": preview.binding_id,
        "owner_capability": preview.owner_capability,
        "proposal_digest": proposal_digest(preview.proposal_ref),
        "resource_ref": preview.resource_ref,
        "exact_change": preview.exact_change,
        "expected_postcondition": preview.expected_postcondition,
        "expires_at_epoch": preview.expires_at_epoch,
        "readiness": preview.readiness.value,
    }
    return hashlib.sha256(_canonical(canonical).encode("utf-8")).hexdigest()


def _readiness_for(payload: Mapping[str, Any], now_epoch: float) -> ProposalReadiness:
    """Classify owner PREPARE payload readiness — fail closed.

    Mandatory governance fields for a safe confirmation: an opaque
    proposal reference and a bounded exact-change preview. Missing or
    malformed mandatory fields -> INVALID, never inferred READY.
    """
    proposal_ref = str(payload.get("proposal_handle") or "").strip()
    exact_change = payload.get("exact_change")
    if not proposal_ref or not isinstance(exact_change, Mapping):
        return ProposalReadiness.INVALID
    expires_at = payload.get("expires_at")
    try:
        expires = float(expires_at) if expires_at is not None else None
    except (TypeError, ValueError):
        return ProposalReadiness.INVALID
    if expires is not None and expires <= now_epoch:
        return ProposalReadiness.EXPIRED
    ready = payload.get("ready")
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
    binding: GovernedWriteBinding,
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
    readiness = _readiness_for(inner, now_epoch)
    expires_raw = inner.get("expires_at")
    try:
        expires = float(expires_raw) if expires_raw is not None else None
    except (TypeError, ValueError):
        expires = None
    return WriteProposalPreview(
        binding_id=binding.binding_id,
        owner_capability=str(
            inner.get("capability") or binding.owner_operation_id
        ).strip(),
        proposal_ref=str(inner.get("proposal_handle") or "").strip(),
        readiness=readiness,
        specialist_id=specialist_id,
        correlation_id=correlation_id,
        observed_at=observed_at,
        resource_ref=(
            str(inner.get("resource_id")).strip()
            if inner.get("resource_id") is not None
            else None
        ),
        exact_change=(
            inner.get("exact_change")
            if isinstance(inner.get("exact_change"), Mapping)
            else None
        ),
        validation_summary=(
            inner.get("validation_result")
            if isinstance(inner.get("validation_result"), Mapping)
            else None
        ),
        consequential_impact=(
            inner.get("consequential_impact")
            if isinstance(inner.get("consequential_impact"), Mapping)
            else None
        ),
        confirmation_requirement=(
            inner.get("confirmation_requirement")
            if isinstance(inner.get("confirmation_requirement"), Mapping)
            else None
        ),
        expected_postcondition=(
            inner.get("expected_postcondition")
            if isinstance(inner.get("expected_postcondition"), Mapping)
            else None
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
    if confirmation.binding_id != preview.binding_id:
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
    binding: GovernedWriteBinding | None,
    preview: WriteProposalPreview | None,
    confirmation: ConfirmationRecord | None,
    now_epoch: float,
) -> WriteGateDecision:
    """Decide whether a governed write may continue toward a future ACT.

    Fail-closed ordering: unknown/disabled binding -> not-ready or
    expired preview -> missing/mismatched/rejected confirmation ->
    READY_FOR_LIVE_REVALIDATION at most. No state here authorizes ACT.
    """
    if binding is None:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.UNKNOWN_BINDING,),
        )
    if not binding.enabled:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.BINDING_DISABLED,),
            binding_id=binding.binding_id,
        )
    if preview is None or preview.readiness is ProposalReadiness.INVALID:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_NOT_READY,),
            binding_id=binding.binding_id,
        )
    if preview.readiness is ProposalReadiness.EXPIRED or (
        preview.expires_at_epoch is not None
        and preview.expires_at_epoch <= now_epoch
    ):
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_EXPIRED,),
            binding_id=binding.binding_id,
        )
    if preview.readiness is not ProposalReadiness.READY:
        return WriteGateDecision(
            status=WriteGateStatus.BLOCKED,
            reason_codes=(WriteGateReason.PROPOSAL_NOT_READY,),
            binding_id=binding.binding_id,
        )
    if binding.confirmation_required and confirmation is None:
        return WriteGateDecision(
            status=WriteGateStatus.REQUIRES_CONFIRMATION,
            reason_codes=(WriteGateReason.CONFIRMATION_MISSING,),
            binding_id=binding.binding_id,
        )
    if confirmation is not None:
        if confirmation.state is ConfirmationState.REJECTED:
            return WriteGateDecision(
                status=WriteGateStatus.REJECTED,
                reason_codes=(WriteGateReason.USER_REJECTED,),
                binding_id=binding.binding_id,
            )
        if confirmation.state is not ConfirmationState.CONFIRMED:
            return WriteGateDecision(
                status=WriteGateStatus.BLOCKED,
                reason_codes=(WriteGateReason.CONFIRMATION_MISMATCH,),
                binding_id=binding.binding_id,
            )
    # Strongest foundation state: the write may continue only to the
    # future ACT boundary where live Core AuthZ + Domain revalidation
    # MUST occur. This is never ACT_AUTHORIZED.
    return WriteGateDecision(
        status=WriteGateStatus.READY_FOR_LIVE_REVALIDATION,
        reason_codes=(
            WriteGateReason.LIVE_AUTHZ_REQUIRED,
            WriteGateReason.DOMAIN_REVALIDATION_REQUIRED,
        ),
        binding_id=binding.binding_id,
        live_core_authz_required=True,
        domain_revalidation_required=True,
    )


def project_write_outcome(
    *,
    binding: GovernedWriteBinding,
    owner_payload: Mapping[str, Any],
    specialist_id: str,
    correlation_id: str,
    occurred_at: str,
    limitations: tuple[str, ...] = (),
) -> WriteOutcomeProjection:
    """Project a future owner ACT result into the bounded outcome.

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
        binding_id=binding.binding_id,
        specialist_id=specialist_id,
        owner_capability=str(
            inner.get("capability") or binding.owner_operation_id
        ).strip(),
        correlation_id=correlation_id,
        occurred_at=occurred_at,
        verified=bool(verified is True),
        postcondition_summary=(
            postcondition if isinstance(postcondition, Mapping) else None
        ),
        limitations=limitations,
    )
