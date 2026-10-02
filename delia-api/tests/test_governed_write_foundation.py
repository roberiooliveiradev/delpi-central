"""Governed-write foundation tests — contracts, gates, adversarial.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): the
static write-binding registry is superseded — the specialist owns
capability existence/pairing via live tools/list. These tests lock the
generic governance semantics bound to a live ``capability_ref``
(``specialist_id.remote_name``): preview projection, exact-preview
confirmation binding, fail-closed continuation gate, owner-authoritative
outcome projection and digest-only audit.
"""

from __future__ import annotations

import ast
import dataclasses
import uuid
from pathlib import Path

import pytest

from app.domain.governed_write import (
    ConfirmationDecision,
    ConfirmationReason,
    ConfirmationState,
    ProposalReadiness,
    StructuredConfirmation,
    WriteAuditStage,
    WriteDecisionAuditRecord,
    WriteGateReason,
    WriteGateStatus,
    WriteOutcomeStatus,
    WriteProposalPreview,
    bind_confirmation,
    evaluate_write_continuation,
    preview_fingerprint,
    project_proposal_preview,
    project_write_outcome,
    proposal_digest,
)


NOW = 1_700_000_000.0
FUTURE = NOW + 300.0
CAPABILITY_REF = "teo.prepare_record_change"


def _owner_prepare_payload(**overrides) -> dict:
    payload = {
        "proposal_handle": "hmac-signed-opaque-handle",
        "capability": "update_record",
        "resource_id": "record-1",
        "exact_change": {"entity": "record", "id": "1", "set": {"x": 2}},
        "validation_result": {"ready": True},
        "consequential_impact": {"rows": 1},
        "confirmation_requirement": {"required": True},
        "expected_postcondition": {"record": {"x": 2}},
        "expires_at": FUTURE,
        "ready": True,
    }
    payload.update(overrides)
    return payload


def _preview(**overrides) -> WriteProposalPreview:
    payload = _owner_prepare_payload()
    payload.update(overrides.pop("payload_overrides", {}))
    preview = project_proposal_preview(
        capability_ref=CAPABILITY_REF,
        remote_capability="prepare_record_change",
        owner_payload=payload,
        specialist_id="teo",
        correlation_id="corr-1",
        observed_at="2026-01-01T00:00:00+00:00",
        now_epoch=NOW,
    )
    if overrides:
        preview = dataclasses.replace(preview, **overrides)
    return preview


def _confirmation(preview, **overrides) -> StructuredConfirmation:
    args = dict(
        actor_user_id="user-1",
        session_id="sess-1",
        capability_ref=preview.capability_ref,
        proposal_digest=proposal_digest(preview.proposal_ref),
        preview_fingerprint=preview_fingerprint(preview),
        decision=ConfirmationDecision.CONFIRM,
        occurred_at_epoch=NOW + 10,
    )
    args.update(overrides)
    return StructuredConfirmation(**args)


def _bound(preview, confirmation=None, **kw):
    return bind_confirmation(
        preview=preview,
        confirmation=confirmation or _confirmation(preview),
        expected_actor_id=kw.get("actor", "user-1"),
        expected_session_id=kw.get("session", "sess-1"),
        now_epoch=kw.get("now", NOW + 20),
    )


def _gate(preview=None, confirmation=None, **kw):
    return evaluate_write_continuation(
        capability_live=kw.get("capability_live", True),
        confirmation_required=kw.get("confirmation_required", True),
        preview=preview if preview is not None else _preview(),
        confirmation=confirmation,
        now_epoch=kw.get("now", NOW),
    )


# ------------------------------------------------------------ live surface


def test_capability_ref_is_a_live_reference_not_a_registry_key():
    """``capability_ref`` is the live ``specialist_id.remote_name``
    identity — there is no local registry to resolve it against."""
    p = _preview()
    assert p.capability_ref == "teo.prepare_record_change"
    assert p.authorizes_act() is False


def test_capability_not_live_blocks_at_gate():
    """Capability absent from the fresh live surface -> BLOCKED."""
    d = evaluate_write_continuation(
        capability_live=False,
        confirmation_required=True,
        preview=_preview(),
        confirmation=None,
        now_epoch=NOW,
    )
    assert d.status is WriteGateStatus.BLOCKED
    assert WriteGateReason.CAPABILITY_NOT_LIVE in d.reason_codes
    assert d.authorizes_act() is False


def test_no_local_write_registry_exists():
    """The superseded static registry symbols must not exist."""
    import app.domain.governed_write as pkg
    import app.domain.governed_write.rules as rules
    import app.domain.governed_write.model as model

    for module in (pkg, rules, model):
        for name in (
            "GOVERNED_WRITE_BINDINGS",
            "GovernedWriteBinding",
            "write_binding_for",
        ):
            assert not hasattr(module, name), f"{module.__name__}.{name}"


# ---------------------------------------------------------------- preview


def test_valid_ready_preview_projects_all_governance_fields():
    p = _preview()
    assert p.readiness is ProposalReadiness.READY
    assert p.proposal_ref == "hmac-signed-opaque-handle"
    assert p.exact_change == {"entity": "record", "id": "1", "set": {"x": 2}}
    assert p.expected_postcondition == {"record": {"x": 2}}
    assert p.expires_at_epoch == FUTURE
    assert p.authorizes_act() is False


def test_preview_not_ready_when_validation_not_ready():
    p = _preview(payload_overrides={"validation_result": {"ready": False}})
    assert p.readiness is ProposalReadiness.NOT_READY


def test_preview_not_ready_when_ready_false():
    p = _preview(payload_overrides={"ready": False})
    assert p.readiness is ProposalReadiness.NOT_READY


def test_preview_expired():
    p = _preview(payload_overrides={"expires_at": NOW - 1})
    assert p.readiness is ProposalReadiness.EXPIRED


def test_preview_invalid_without_handle():
    p = _preview(payload_overrides={"proposal_handle": ""})
    assert p.readiness is ProposalReadiness.INVALID


def test_preview_invalid_without_exact_change():
    p = _preview(payload_overrides={"exact_change": None})
    assert p.readiness is ProposalReadiness.INVALID


def test_preview_unknown_when_readiness_inconclusive():
    p = _preview(
        payload_overrides={"ready": None, "validation_result": None}
    )
    assert p.readiness is ProposalReadiness.UNKNOWN


def test_preview_unwraps_owner_data_envelope():
    p = project_proposal_preview(
        capability_ref=CAPABILITY_REF,
        remote_capability="prepare_record_change",
        owner_payload={"success": True, "data": _owner_prepare_payload()},
        specialist_id="teo",
        correlation_id="c",
        observed_at="t",
        now_epoch=NOW,
    )
    assert p.readiness is ProposalReadiness.READY


def test_handle_opacity_digest_only_for_correlation():
    p = _preview()
    digest = proposal_digest(p.proposal_ref)
    assert digest != p.proposal_ref
    assert len(digest) == 64
    assert p.proposal_ref not in digest


def test_preview_fingerprint_deterministic():
    a, b = _preview(), _preview()
    assert preview_fingerprint(a) == preview_fingerprint(b)


def test_preview_fingerprint_changes_on_meaningful_change():
    a = _preview()
    b = _preview(payload_overrides={"exact_change": {"x": 3}})
    c = _preview(payload_overrides={"proposal_handle": "other-handle"})
    assert preview_fingerprint(a) != preview_fingerprint(b)
    assert preview_fingerprint(a) != preview_fingerprint(c)


def test_model_generated_payload_cannot_become_ready_proposal():
    fake = {"proposal_handle": "model-invented", "exact_change": {"x": 1},
            "ready": True, "expires_at": FUTURE}
    p = project_proposal_preview(
        capability_ref=CAPABILITY_REF,
        remote_capability="prepare_record_change",
        owner_payload=fake,
        specialist_id="teo",
        correlation_id="c",
        observed_at="t",
        now_epoch=NOW,
    )
    # A model-shaped payload projects as untrusted data; it carries no
    # owner authority — authorizes_act stays False either way.
    assert p.authorizes_act() is False


# ---------------------------------------------------------------- confirmation


def test_exact_match_confirmation_binds():
    p = _preview()
    r = _bound(p)
    assert r.state is ConfirmationState.CONFIRMED
    assert r.reason_codes == (ConfirmationReason.EXACT_PREVIEW_CONFIRMED,)
    assert r.authorizes_act() is False


def test_confirmation_actor_mismatch_rejects():
    p = _preview()
    r = _bound(p, actor="other-user")
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.ACTOR_MISMATCH in r.reason_codes


def test_confirmation_session_mismatch_rejects():
    p = _preview()
    r = _bound(p, session="other-session")
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.SESSION_MISMATCH in r.reason_codes


def test_confirmation_wrong_capability_ref_rejects():
    p = _preview()
    c = _confirmation(p, capability_ref="teo.other_capability")
    r = _bound(p, confirmation=c)
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.BINDING_MISMATCH in r.reason_codes


def test_confirmation_wrong_proposal_rejects():
    p = _preview()
    c = _confirmation(p, proposal_digest="0" * 64)
    r = _bound(p, confirmation=c)
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.PROPOSAL_MISMATCH in r.reason_codes


def test_confirmation_changed_preview_rejects():
    p = _preview()
    changed = _preview(payload_overrides={"exact_change": {"x": 9}})
    c = _confirmation(changed)
    r = _bound(p, confirmation=c)
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.PREVIEW_CHANGED in r.reason_codes


def test_confirmation_expired_preview_rejects():
    p = _preview(payload_overrides={"expires_at": NOW - 1})
    r = _bound(p)
    assert r.state in (
        ConfirmationState.EXPIRED,
        ConfirmationState.INVALIDATED,
    )
    assert ConfirmationReason.PROPOSAL_EXPIRED in r.reason_codes
    assert r.state is not ConfirmationState.CONFIRMED


def test_confirmation_not_ready_preview_rejects():
    p = _preview(payload_overrides={"ready": False})
    r = _bound(p)
    assert r.state is ConfirmationState.INVALIDATED
    assert ConfirmationReason.PROPOSAL_NOT_READY in r.reason_codes


def test_explicit_reject():
    p = _preview()
    c = _confirmation(p, decision=ConfirmationDecision.REJECT)
    r = _bound(p, confirmation=c)
    assert r.state is ConfirmationState.REJECTED
    assert ConfirmationReason.USER_REJECTED in r.reason_codes


def test_replayed_confirmation_cannot_bind_other_proposal():
    p1 = _preview()
    p2 = _preview(payload_overrides={"proposal_handle": "handle-b"})
    c = _confirmation(p1)
    r = _bound(p2, confirmation=c)
    assert r.state is not ConfirmationState.CONFIRMED


def test_confirmation_requires_all_fields():
    with pytest.raises(ValueError):
        StructuredConfirmation(
            actor_user_id="",
            session_id="s",
            capability_ref="c",
            proposal_digest="d",
            preview_fingerprint="f",
            decision=ConfirmationDecision.CONFIRM,
            occurred_at_epoch=NOW,
        )


# ---------------------------------------------------------------- decision gate


def test_gate_requires_confirmation_when_missing():
    d = _gate()
    assert d.status is WriteGateStatus.REQUIRES_CONFIRMATION
    assert WriteGateReason.CONFIRMATION_MISSING in d.reason_codes


def test_gate_blocks_not_ready_proposal():
    d = _gate(preview=_preview(payload_overrides={"ready": False}))
    assert d.status is WriteGateStatus.BLOCKED
    assert WriteGateReason.PROPOSAL_NOT_READY in d.reason_codes


def test_gate_blocks_expired_proposal():
    d = _gate(preview=_preview(payload_overrides={"expires_at": NOW - 1}))
    assert d.status is WriteGateStatus.BLOCKED
    assert WriteGateReason.PROPOSAL_EXPIRED in d.reason_codes


def test_gate_blocks_expired_by_clock_even_if_marked_ready():
    d = _gate(now=FUTURE + 1)
    assert d.status is WriteGateStatus.BLOCKED


def test_gate_rejects_user_rejection():
    p = _preview()
    c = _confirmation(p, decision=ConfirmationDecision.REJECT)
    r = _bound(p, confirmation=c)
    d = _gate(preview=p, confirmation=r)
    assert d.status is WriteGateStatus.REJECTED
    assert WriteGateReason.USER_REJECTED in d.reason_codes


def test_gate_blocks_invalidated_confirmation():
    p = _preview()
    c = _confirmation(p, actor_user_id="someone-else")
    r = _bound(p, confirmation=c)
    d = _gate(preview=p, confirmation=r)
    assert d.status is WriteGateStatus.BLOCKED
    assert WriteGateReason.CONFIRMATION_MISMATCH in d.reason_codes


def test_gate_strongest_state_is_ready_for_live_revalidation():
    p = _preview()
    r = _bound(p)
    d = _gate(preview=p, confirmation=r)
    assert d.status is WriteGateStatus.READY_FOR_LIVE_REVALIDATION
    assert WriteGateReason.LIVE_AUTHZ_REQUIRED in d.reason_codes
    assert WriteGateReason.DOMAIN_REVALIDATION_REQUIRED in d.reason_codes
    assert d.live_core_authz_required is True
    assert d.domain_revalidation_required is True
    assert d.authorizes_act() is False
    assert d.grants_authorization() is False


def test_gate_ready_state_cannot_exist_without_live_revalidation():
    with pytest.raises(ValueError):
        from app.domain.governed_write import WriteGateDecision

        WriteGateDecision(
            status=WriteGateStatus.READY_FOR_LIVE_REVALIDATION,
            live_core_authz_required=False,
        )


def test_gate_no_act_authorized_state_exists():
    assert "ACT_AUTHORIZED" not in {s.name for s in WriteGateStatus}
    assert "AUTHORIZED_AND_EXECUTE" not in {s.name for s in WriteGateStatus}


# ---------------------------------------------------------------- outcome


def _outcome(payload, **kw):
    return project_write_outcome(
        capability_ref="teo.commit_proposal",
        remote_capability="commit_proposal",
        owner_payload=payload,
        specialist_id="teo",
        correlation_id="corr",
        occurred_at="2026-01-01T00:00:00+00:00",
        **kw,
    )


def test_outcome_verified_requires_owner_verified_flag():
    o = _outcome({"success": True, "verified": True,
                  "data": None, "capability": "update_record"})
    assert o.status is WriteOutcomeStatus.VERIFIED
    assert o.verified is True


def test_outcome_verified_inside_data_envelope():
    o = _outcome({"data": {"verified": True, "capability": "update_record",
                           "verified_payload": {"x": 2}}})
    assert o.status is WriteOutcomeStatus.VERIFIED


def test_outcome_technical_success_unverified_is_not_verified():
    o = _outcome({"success": True, "verified": False})
    assert o.status is WriteOutcomeStatus.OUTCOME_VERIFICATION_FAILED
    assert o.verified is False


def test_outcome_technical_success_without_verified_is_reported_only():
    o = _outcome({"success": True})
    assert o.status is WriteOutcomeStatus.EXECUTION_REPORTED
    assert o.verified is False


def test_outcome_failure():
    o = _outcome({"success": False})
    assert o.status is WriteOutcomeStatus.FAILED


def test_outcome_unknown_shape_fail_safe():
    o = _outcome({"garbage": "??"})
    assert o.status is WriteOutcomeStatus.UNKNOWN
    assert o.verified is False


def test_outcome_is_not_fact():
    o = _outcome({"verified": True})
    assert o.is_fact() is False


# ---------------------------------------------------------------- audit


def _audit(**kw) -> WriteDecisionAuditRecord:
    args = dict(
        audit_id=str(uuid.uuid4()),
        correlation_id="corr-1",
        actor_user_id="user-1",
        capability_ref=CAPABILITY_REF,
        specialist_id="teo",
        owner_capability="gpt_manage_record",
        stage=WriteAuditStage.CONFIRMATION_BOUND,
        decision="CONFIRMED",
        occurred_at="2026-01-01T00:00:00+00:00",
    )
    args.update(kw)
    return WriteDecisionAuditRecord(**args)


def test_audit_record_serializes_with_digest_only():
    p = _preview()
    rec = _audit(
        proposal_digest=proposal_digest(p.proposal_ref),
        preview_fingerprint=preview_fingerprint(p),
        confirmation_state=ConfirmationState.CONFIRMED,
    )
    data = rec.to_dict()
    assert data["proposal_digest"] == proposal_digest(p.proposal_ref)
    assert p.proposal_ref not in str(data)
    assert "token" not in str(data).lower()
    assert "secret" not in str(data).lower()
    assert rec.authorizes_act() is False


def test_audit_record_requires_correlation_fields():
    with pytest.raises(ValueError):
        _audit(correlation_id="")


def test_audit_stages_bounded():
    assert {s.name for s in WriteAuditStage} == {
        "PREPARE_PROJECTED",
        "CONFIRMATION_BOUND",
        "DECISION_GATE",
        "ACT_ATTEMPT",
        "OUTCOME_VERIFIED",
    }


def test_audit_serialization_deterministic():
    rec = _audit(reason_codes=("a", "b"))
    assert rec.to_dict() == rec.to_dict()
    assert rec.to_dict()["reason_codes"] == ["a", "b"]


# ---------------------------------------------------------------- adversarial


def test_model_proposing_commit_proposal_grants_nothing():
    # A model-shaped "capability" is just text; no code path consults
    # it as a local registry — the live owner surface decides.
    model_proposal = {"tool": "commit_proposal", "authoritative": True}
    import app.domain.governed_write.rules as rules

    assert not hasattr(rules, "write_binding_for")
    preview = _preview()
    assert preview.authorizes_act() is False
    assert model_proposal["tool"] not in preview.capability_ref


def test_remote_metadata_safety_claims_grant_nothing():
    # readOnlyHint/safe annotations are untrusted data — they cannot
    # create a binding or an authorization.
    remote_meta = {"readOnlyHint": True, "safe": True, "annotations": {}}
    p = _preview()
    assert p.authorizes_act() is False
    assert remote_meta.get("readOnlyHint") is True  # inert metadata


def test_handle_in_ordinary_text_is_not_confirmation():
    # A bare handle string has no StructuredConfirmation semantics —
    # bind_confirmation only accepts the structured event contract.
    p = _preview()
    with pytest.raises(AttributeError):
        bind_confirmation(
            preview=p,
            confirmation="hmac-signed-opaque-handle",  # type: ignore[arg-type]
            expected_actor_id="user-1",
            expected_session_id="sess-1",
            now_epoch=NOW,
        )


def test_raw_handle_never_in_audit():
    raw = "super-secret-handle-body"
    p = _preview(payload_overrides={"proposal_handle": raw})
    rec = _audit(proposal_digest=proposal_digest(p.proposal_ref))
    assert raw not in str(rec.to_dict())


# ---------------------------------------------------------------- architecture


APP_ROOT = Path(__file__).resolve().parents[1] / "app"

FORBIDDEN_IMPORTS = (
    "flask", "fastapi", "sqlalchemy", "httpx", "requests", "openai",
    "mcp", "keycloak", "redis",
)

FORBIDDEN_TYPES = {
    "GovernedWriteEngine",
    "GenericWriteOrchestrator",
    "AutomationHubService",
    "WorkflowEngine",
    "DecisionPlatform",
    "AuditMicroservice",
    "WriteRegistryService",
    # The superseded static registry type must never return.
    "GovernedWriteBinding",
}

FORBIDDEN_FIELDS = {
    "endpoint", "url", "http_method", "selector", "access_token",
    "refresh_token", "api_key", "client_secret", "credential",
    "chain_of_thought", "authorization_header", "prompt",
}


def test_governed_write_domain_has_no_infra_or_provider_imports():
    pkg = APP_ROOT / "domain" / "governed_write"
    for path in pkg.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.lower() for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").lower()]
            else:
                continue
            joined = " ".join(names)
            for fragment in FORBIDDEN_IMPORTS:
                assert fragment not in joined, f"{path} imports {fragment}"


def test_governed_write_no_engine_or_generic_abstractions():
    for path in (APP_ROOT / "domain" / "governed_write").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPES, path


def test_governed_write_models_have_no_mechanics_or_secret_fields():
    from dataclasses import fields as dc_fields
    from app.domain.governed_write import model as m

    for cls_name in (
        "WriteProposalPreview",
        "StructuredConfirmation",
        "ConfirmationRecord",
        "WriteGateDecision",
        "WriteOutcomeProjection",
        "WriteDecisionAuditRecord",
    ):
        names = {f.name.lower() for f in dc_fields(getattr(m, cls_name))}
        assert names.isdisjoint(FORBIDDEN_FIELDS), cls_name


def test_governed_write_has_no_specialist_specific_branches():
    src = (APP_ROOT / "domain" / "governed_write" / "rules.py").read_text()
    # no teo/vista/davi-specific branching inside generic rules
    for marker in ("if specialist", "== 'teo'", '== "teo"',
                   "== 'vista'", '== "vista"', "== 'davi'", '== "davi"'):
        assert marker not in src


def test_governed_write_domain_has_no_invocation_paths():
    # The domain projects payloads and decides gates; wire invocation
    # belongs to the application/infrastructure layers.
    for path in (APP_ROOT / "domain" / "governed_write").rglob("*.py"):
        src = path.read_text()
        assert "SpecialistInterop" not in src
        assert "invoke" not in src
