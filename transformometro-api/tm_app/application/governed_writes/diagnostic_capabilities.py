"""Diagnostic V1 — governed PREPARE/ACT capability plumbing.

Two capabilities integrate with the canonical ``GovernedWriteOrchestrator``:

    create_diagnostic  — aggregate creation anchored to an existing Revision
    manage_diagnostic  — one closed-allowlist ``action`` against an existing
                         aggregate (entity additions, lifecycle transitions,
                         effective-validation marks)

This module holds explicit per-action payload parsing — no dynamic dispatch,
no arbitrary payloads. PREPARE seals the normalized ``exact_change``;
ACT rebuilds domain objects from the sealed payload and delegates to the
canonical ``DiagnosticWriteUseCase`` (which performs fresh AuthZ, domain
mutation, optimistic save, authoritative read-back and postcondition).
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Callable, NamedTuple

from tm_app.application.governed_writes.errors import (
    BUSINESS_RULE,
    CONFLICT,
    FORBIDDEN,
    INTERNAL,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.proposal import fingerprint
from tm_app.application.ports.authorization_port import (
    AuthorizationPort,
    DiagnosticAuthorizationError,
)
from tm_app.application.ports.evidence_reader_port import EvidenceReaderPort
from tm_app.application.ports.revision_reader_port import RevisionReaderPort
from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.application.use_cases.diagnostic_read import _snapshot
from tm_app.application.use_cases.diagnostic_write import (
    DiagnosticWriteError,
    DiagnosticWriteUseCase,
)
from tm_app.domain.diagnostic.diagnostic import (
    CausalLink,
    Diagnostic,
    DiagnosticConclusion,
    DiagnosticError,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    FindingRole,
    EpistemicState,
    Hypothesis,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
)
from tm_app.domain.ports.diagnostic_repository_port import (
    DiagnosticRepositoryPort,
)


class DiagnosticWriteStack(NamedTuple):
    """Composition bundle: canonical write path + read ports for PREPARE."""

    use_case: DiagnosticWriteUseCase
    diagnostics: DiagnosticRepositoryPort
    revisions: RevisionReaderPort
    evidence: EvidenceReaderPort


CREATE_CAPABILITY = "create_diagnostic"
MANAGE_CAPABILITY = "manage_diagnostic"
DIAGNOSTIC_CAPABILITIES = frozenset({CREATE_CAPABILITY, MANAGE_CAPABILITY})

ENTITY_ACTIONS = frozenset(
    {
        "add_finding",
        "add_hypothesis",
        "add_causal_link",
        "add_evidence_link",
        "add_conclusion",
    }
)
HYPOTHESIS_LIFECYCLE_ACTIONS = frozenset(
    {"validate_hypothesis", "reject_hypothesis", "supersede_hypothesis"}
)
HYPOTHESIS_MARK_ACTIONS = frozenset(
    {"mark_hypothesis_stale_evidence", "mark_hypothesis_revalidation_required"}
)
CONCLUSION_LIFECYCLE_ACTIONS = frozenset(
    {"validate_conclusion", "reject_conclusion", "supersede_conclusion"}
)
MANAGE_ACTIONS = (
    ENTITY_ACTIONS
    | HYPOTHESIS_LIFECYCLE_ACTIONS
    | HYPOTHESIS_MARK_ACTIONS
    | CONCLUSION_LIFECYCLE_ACTIONS
)


def _raise(message: str, *, code: str, status_code: int) -> None:
    raise GovernedWriteError(message, code=code, status_code=status_code)


# ---------------------------------------------------------------------------
# PREPARE authorization — normal context is sufficient to *formulate* a
# proposal; ACT re-verifies fresh inside the use case. Service principals
# can never formulate material writes (canonical marker required).
# ---------------------------------------------------------------------------


def require_prepare_authz(request: Any) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        _raise("Usuário não autenticado.", code="unauthenticated", status_code=401)
    if getattr(user, "principal_type", None) != "user":
        _raise(
            "Diagnostic writes exigem principal end-user.",
            code=FORBIDDEN,
            status_code=403,
        )
    try:
        TransformometroAuthorizationPolicy().require_access(user)
    except AuthorizationDenied as exc:
        _raise(
            "Sem permissão transformometro.access.",
            code=FORBIDDEN,
            status_code=exc.status_code,
        )


# ---------------------------------------------------------------------------
# Payload parsers — explicit per action; domain objects are constructed at
# PREPARE (fail-fast validation) and rebuilt identically at ACT.
# ---------------------------------------------------------------------------


def _req_str(payload: dict, key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        _raise(
            f"Campo obrigatório ausente: {key}.",
            code=VALIDATION,
            status_code=400,
        )
    return value


def _reject_unknown(payload: dict, allowed: set[str]) -> None:
    extra = set(payload) - allowed
    if extra:
        _raise(
            f"Campos não permitidos no payload: {sorted(extra)}.",
            code=VALIDATION,
            status_code=400,
        )


def _parse_provenance(raw: Any) -> Provenance | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        _raise(
            "provenance deve ser objeto {origin, detail?}.",
            code=VALIDATION,
            status_code=400,
        )
    try:
        origin = ProvenanceOrigin(str(raw.get("origin") or "").strip())
    except ValueError:
        _raise(
            "provenance.origin deve ser USER ou TEO.",
            code=VALIDATION,
            status_code=400,
        )
    return Provenance(origin=origin, detail=raw.get("detail"))


def _domain_construct(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except DiagnosticError as exc:
        _raise(str(exc), code=VALIDATION, status_code=400)
    except (ValueError, TypeError) as exc:
        _raise(str(exc), code=VALIDATION, status_code=400)


def _parse_finding(payload: dict) -> Finding:
    _reject_unknown(
        payload, {"finding_id", "statement", "role", "epistemic_state", "provenance"}
    )
    role = payload.get("role")
    epistemic = payload.get("epistemic_state")
    return _domain_construct(
        lambda: Finding(
            finding_id=_req_str(payload, "finding_id"),
            statement=_req_str(payload, "statement"),
            role=FindingRole(str(role)) if role is not None else None,
            epistemic_state=(
                EpistemicState(str(epistemic))
                if epistemic is not None
                else EpistemicState.OBSERVED
            ),
            provenance=_parse_provenance(payload.get("provenance")),
        )
    )


def _parse_hypothesis(payload: dict) -> Hypothesis:
    _reject_unknown(payload, {"hypothesis_id", "statement", "provenance"})
    return _domain_construct(
        lambda: Hypothesis(
            hypothesis_id=_req_str(payload, "hypothesis_id"),
            statement=_req_str(payload, "statement"),
            provenance=_parse_provenance(payload.get("provenance")),
        )
    )


def _parse_causal_link(payload: dict) -> CausalLink:
    _reject_unknown(
        payload, {"link_id", "source_hypothesis_id", "target_id", "relation"}
    )
    if payload.get("relation") not in (None, "CONTRIBUTES_TO"):
        _raise(
            "V1 suporta exclusivamente relation CONTRIBUTES_TO.",
            code=VALIDATION,
            status_code=400,
        )
    return _domain_construct(
        lambda: CausalLink(
            link_id=_req_str(payload, "link_id"),
            source_hypothesis_id=_req_str(payload, "source_hypothesis_id"),
            target_id=_req_str(payload, "target_id"),
        )
    )


def _parse_evidence_link(payload: dict) -> EvidenceLink:
    _reject_unknown(
        payload, {"link_id", "evidence_id", "relation", "target_id"}
    )
    try:
        relation = EvidenceRelation(_req_str(payload, "relation"))
    except ValueError:
        _raise(
            "relation deve ser SUPPORTS, CONTEXTUALIZES ou CONTRADICTS.",
            code=VALIDATION,
            status_code=400,
        )
    return _domain_construct(
        lambda: EvidenceLink(
            link_id=_req_str(payload, "link_id"),
            evidence_id=_req_str(payload, "evidence_id"),
            relation=relation,
            target_id=payload.get("target_id"),
        )
    )


def _parse_conclusion(payload: dict) -> DiagnosticConclusion:
    _reject_unknown(
        payload,
        {
            "conclusion_id",
            "statement",
            "rationale",
            "hypothesis_ids",
            "finding_ids",
            "root_cause_hypothesis_id",
            "provenance",
        },
    )
    root_id = payload.get("root_cause_hypothesis_id")
    return _domain_construct(
        lambda: DiagnosticConclusion(
            conclusion_id=_req_str(payload, "conclusion_id"),
            statement=_req_str(payload, "statement"),
            rationale=payload.get("rationale"),
            hypothesis_ids=tuple(payload.get("hypothesis_ids") or ()),
            finding_ids=tuple(payload.get("finding_ids") or ()),
            root_cause=(
                RootCauseDesignation(str(root_id)) if root_id else None
            ),
            provenance=_parse_provenance(payload.get("provenance")),
        )
    )


def _parse_target(payload: dict, key: str, allowed: set[str]) -> dict[str, Any]:
    _reject_unknown(payload, allowed)
    normalized: dict[str, Any] = {key: _req_str(payload, key)}
    note = payload.get("note")
    if note is not None:
        normalized["note"] = str(note)
    return normalized


def _normalize_provenance(provenance: Provenance | None) -> dict | None:
    if provenance is None:
        return None
    return {"origin": provenance.origin.value, "detail": provenance.detail}


def _normalize_entity(action: str, entity: Any) -> dict[str, Any]:
    """Seal a domain entity as a plain JSON-safe payload.

    Only caller-owned fields are carried — kernel-managed state (lifecycle,
    epistemic_state, effective_validation, validation_history, version)
    never enters the sealed change.
    """
    if action == "add_finding":
        return {
            "finding_id": entity.finding_id,
            "statement": entity.statement,
            "role": entity.role.value if entity.role else None,
            "epistemic_state": entity.epistemic_state.value,
            "provenance": _normalize_provenance(entity.provenance),
        }
    if action == "add_hypothesis":
        return {
            "hypothesis_id": entity.hypothesis_id,
            "statement": entity.statement,
            "provenance": _normalize_provenance(entity.provenance),
        }
    if action == "add_causal_link":
        return {
            "link_id": entity.link_id,
            "source_hypothesis_id": entity.source_hypothesis_id,
            "target_id": entity.target_id,
        }
    if action == "add_evidence_link":
        return {
            "link_id": entity.link_id,
            "evidence_id": entity.evidence_id,
            "relation": entity.relation.value,
            "target_id": entity.target_id,
        }
    return {
        "conclusion_id": entity.conclusion_id,
        "statement": entity.statement,
        "rationale": entity.rationale,
        "hypothesis_ids": list(entity.hypothesis_ids),
        "finding_ids": list(entity.finding_ids),
        "root_cause_hypothesis_id": (
            entity.root_cause.hypothesis_id if entity.root_cause else None
        ),
        "provenance": _normalize_provenance(entity.provenance),
    }


# action → (entity builder | normalized-payload builder)
_ENTITY_PARSERS: dict[str, Callable[[dict], Any]] = {
    "add_finding": _parse_finding,
    "add_hypothesis": _parse_hypothesis,
    "add_causal_link": _parse_causal_link,
    "add_evidence_link": _parse_evidence_link,
    "add_conclusion": _parse_conclusion,
}


def parse_manage_payload(action: str, payload: dict) -> dict[str, Any]:
    """Validate the caller payload and return the sealed normalized change.

    Entity payloads are normalized to plain JSON-safe fields; ACT rebuilds
    the same domain objects deterministically.
    """
    if action not in MANAGE_ACTIONS:
        _raise(
            f"Action '{action}' não é uma mutation Diagnostic permitida.",
            code=VALIDATION,
            status_code=400,
        )
    if action in _ENTITY_PARSERS:
        return _normalize_entity(action, _ENTITY_PARSERS[action](payload))
    if action in HYPOTHESIS_LIFECYCLE_ACTIONS | HYPOTHESIS_MARK_ACTIONS:
        return _parse_target(
            payload, "hypothesis_id", {"hypothesis_id", "note"}
        )
    return _parse_target(payload, "conclusion_id", {"conclusion_id", "note"})


# ---------------------------------------------------------------------------
# PREPARE
# ---------------------------------------------------------------------------


def prepare_create(stack: DiagnosticWriteStack, args: dict) -> dict[str, Any]:
    diagnostic_id = _req_str(args, "diagnostic_id")
    revision_id = _req_str(args, "revision_id")
    problem_statement = _req_str(args, "problem_statement")
    provenance = _parse_provenance(args.get("provenance"))

    revision = stack.revisions.get(revision_id)
    if revision is None:
        _raise(
            "diagnostic.revision_not_found: revision inexistente.",
            code=NOT_FOUND,
            status_code=404,
        )
    if stack.diagnostics.get(diagnostic_id) is not None:
        _raise(
            f"diagnostic_id já existente: {diagnostic_id}.",
            code=CONFLICT,
            status_code=409,
        )

    return {
        "resource_type": "diagnostic",
        "resource_id": diagnostic_id,
        "current_state_fingerprint": fingerprint(
            {
                "diagnostic_id": diagnostic_id,
                "exists": False,
                "revision_id": revision_id,
                "revision": asdict(revision),
            }
        ),
        "exact_change": {
            "action": "create",
            "diagnostic_id": diagnostic_id,
            "revision_id": revision_id,
            "problem_statement": problem_statement,
            "provenance": (
                {
                    "origin": provenance.origin.value,
                    "detail": provenance.detail,
                }
                if provenance is not None
                else None
            ),
        },
        "validation_result": {"ready": True},
        "consequential_impact": {
            "persists": True,
            "operation": "create_diagnostic",
        },
        "confirmation_requirement": {"explicit_user_confirmation": True},
        "expected_postcondition": {
            "type": "diagnostic_created",
            "diagnostic_id": diagnostic_id,
            "revision_id": revision_id,
        },
    }


def prepare_manage(stack: DiagnosticWriteStack, args: dict) -> dict[str, Any]:
    diagnostic_id = _req_str(args, "diagnostic_id")
    action = str(args.get("action") or "").strip()
    if action not in MANAGE_ACTIONS:
        _raise(
            f"Action '{action}' não é permitida em manage_diagnostic.",
            code=VALIDATION,
            status_code=400,
        )
    diagnostic = stack.diagnostics.get(diagnostic_id)
    if diagnostic is None:
        _raise(
            "diagnostic.not_found: aggregate inexistente.",
            code=NOT_FOUND,
            status_code=404,
        )
    normalized = parse_manage_payload(action, dict(args.get("payload") or {}))

    validation: dict[str, Any] = {"ready": True}
    # Honest PREPARE: surface the revision-scope evidence check early so an
    # unresolvable link never reaches ACT as a ready proposal.
    if action == "add_evidence_link":
        resolved = {
            ref.evidence_id
            for ref in stack.evidence.list_by_revision(diagnostic.revision_id)
        }
        if normalized["evidence_id"] not in resolved:
            validation = {
                "ready": False,
                "missing": ["evidence_out_of_revision"],
            }

    return {
        "resource_type": "diagnostic",
        "resource_id": diagnostic_id,
        "current_state_fingerprint": _fingerprint_diagnostic(diagnostic),
        "exact_change": {
            "action": action,
            "diagnostic_id": diagnostic_id,
            "expected_version": diagnostic.version,
            "payload": normalized,
        },
        "validation_result": validation,
        "consequential_impact": {
            "persists": True,
            "operation": f"diagnostic_{action}",
        },
        "confirmation_requirement": {"explicit_user_confirmation": True},
        "expected_postcondition": _postcondition(action, normalized),
    }


def _postcondition(action: str, payload: dict) -> dict[str, Any]:
    if action in ENTITY_ACTIONS:
        return {"type": "entity_present", "action": action, "payload": payload}
    if action == "validate_hypothesis":
        return {"type": "hypothesis_lifecycle", "target": "VALIDATED", **payload}
    if action == "reject_hypothesis":
        return {"type": "hypothesis_lifecycle", "target": "REJECTED", **payload}
    if action == "supersede_hypothesis":
        return {"type": "hypothesis_lifecycle", "target": "SUPERSEDED", **payload}
    if action == "mark_hypothesis_stale_evidence":
        return {
            "type": "hypothesis_effective",
            "target": "STALE_EVIDENCE",
            **payload,
        }
    if action == "mark_hypothesis_revalidation_required":
        return {
            "type": "hypothesis_effective",
            "target": "REVALIDATION_REQUIRED",
            **payload,
        }
    if action == "validate_conclusion":
        return {"type": "conclusion_lifecycle", "target": "VALIDATED", **payload}
    if action == "reject_conclusion":
        return {"type": "conclusion_lifecycle", "target": "REJECTED", **payload}
    return {"type": "conclusion_lifecycle", "target": "SUPERSEDED", **payload}


def _fingerprint_diagnostic(diagnostic: Diagnostic) -> str:
    """Authoritative state fingerprint — any material change breaks it."""
    return fingerprint(asdict(_snapshot(diagnostic)))


def recompute_fingerprint(
    stack: DiagnosticWriteStack, capability: str, change: dict[str, Any]
) -> str:
    if capability == CREATE_CAPABILITY:
        revision = stack.revisions.get(str(change["revision_id"]))
        return fingerprint(
            {
                "diagnostic_id": change["diagnostic_id"],
                "exists": stack.diagnostics.get(str(change["diagnostic_id"]))
                is not None,
                "revision_id": change["revision_id"],
                "revision": asdict(revision) if revision else None,
            }
        )
    diagnostic = stack.diagnostics.get(str(change["diagnostic_id"]))
    if diagnostic is None:
        return fingerprint({"missing_diagnostic": change["diagnostic_id"]})
    return _fingerprint_diagnostic(diagnostic)


# ---------------------------------------------------------------------------
# ACT — canonical write path only (DiagnosticWriteUseCase); fresh AuthZ runs
# inside it. Errors map to stable governed semantics without leaking internals.
# ---------------------------------------------------------------------------


def _map_write_error(exc: Exception) -> GovernedWriteError:
    if isinstance(exc, DiagnosticAuthorizationError):
        status = {
            "diagnostic.authentication_required": 401,
            "diagnostic.authorization_denied": 403,
            "diagnostic.authorization_unavailable": 503,
        }.get(exc.code, 403)
        code = {
            401: "unauthenticated",
            403: FORBIDDEN,
            503: "authorization_unavailable",
        }[status]
        return GovernedWriteError(
            str(exc), code=code, status_code=status, data={"detail": exc.code}
        )
    if isinstance(exc, DiagnosticWriteError):
        status_map = {
            "diagnostic.not_found": (NOT_FOUND, 404),
            "diagnostic.revision_not_found": (NOT_FOUND, 404),
            "diagnostic.evidence_out_of_revision": (BUSINESS_RULE, 422),
            "diagnostic.concurrent_modification": (CONFLICT, 409),
            "diagnostic.outcome_verification_failed": (
                OUTCOME_VERIFICATION_FAILED,
                409,
            ),
            "diagnostic.persistence_error": (INTERNAL, 500),
        }
        code, status = status_map.get(exc.code, (None, None))
        if code is None:
            # Domain-rule codes: state-dependent conflicts vs invalid input.
            if exc.code in {
                "invalid_lifecycle_transition",
                "effective_conclusion_conflict",
            }:
                code, status = BUSINESS_RULE, 409
            else:
                code, status = VALIDATION, 400
        return GovernedWriteError(
            str(exc), code=code, status_code=status, data={"detail": exc.code}
        )
    return GovernedWriteError(str(exc), code=INTERNAL, status_code=500)


def run_sync(coro: Any) -> Any:
    """Execute the async write use case from the sync governed path.

    All current call sites run outside an event loop (sync FastAPI
    handlers run in a threadpool; MCP tools call sync bridges). Inside a
    running loop we fail loudly rather than silently pick wrong semantics.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    coro.close()
    _raise(
        "Diagnostic ACT requires a non-async execution context.",
        code=INTERNAL,
        status_code=500,
    )


def execute(stack: DiagnosticWriteStack, change: dict[str, Any]) -> Any:
    """Re-run the sealed exact_change through the canonical use case."""
    use_case = stack.use_case
    diagnostic_id = str(change["diagnostic_id"])
    action = change["action"]
    payload = dict(change.get("payload") or {})

    try:
        if action == "create":
            return run_sync(
                use_case.create_diagnostic(
                    diagnostic_id=diagnostic_id,
                    revision_id=str(change["revision_id"]),
                    problem_statement=str(change["problem_statement"]),
                    provenance=_parse_provenance(change.get("provenance")),
                )
            )
        if action == "add_finding":
            return run_sync(
                use_case.add_finding(
                    diagnostic_id=diagnostic_id,
                    finding=_parse_finding(payload),
                )
            )
        if action == "add_hypothesis":
            return run_sync(
                use_case.add_hypothesis(
                    diagnostic_id=diagnostic_id,
                    hypothesis=_parse_hypothesis(payload),
                )
            )
        if action == "add_causal_link":
            return run_sync(
                use_case.add_causal_link(
                    diagnostic_id=diagnostic_id,
                    link=_parse_causal_link(payload),
                )
            )
        if action == "add_evidence_link":
            return run_sync(
                use_case.add_evidence_link(
                    diagnostic_id=diagnostic_id,
                    link=_parse_evidence_link(payload),
                )
            )
        if action == "add_conclusion":
            return run_sync(
                use_case.add_conclusion(
                    diagnostic_id=diagnostic_id,
                    conclusion=_parse_conclusion(payload),
                )
            )
        if action in HYPOTHESIS_LIFECYCLE_ACTIONS:
            method = getattr(use_case, action)
            return run_sync(
                method(
                    diagnostic_id=diagnostic_id,
                    hypothesis_id=str(payload["hypothesis_id"]),
                    note=payload.get("note"),
                )
            )
        if action in HYPOTHESIS_MARK_ACTIONS:
            method = getattr(use_case, action)
            return run_sync(
                method(
                    diagnostic_id=diagnostic_id,
                    hypothesis_id=str(payload["hypothesis_id"]),
                )
            )
        method = getattr(use_case, action)
        return run_sync(
            method(
                diagnostic_id=diagnostic_id,
                conclusion_id=str(payload["conclusion_id"]),
                note=payload.get("note"),
            )
        )
    except (
        DiagnosticWriteError,
        DiagnosticAuthorizationError,
        GovernedWriteError,
    ) as exc:
        if isinstance(exc, GovernedWriteError):
            raise
        raise _map_write_error(exc) from exc


# ---------------------------------------------------------------------------
# VERIFY — external confirmation that the returned read model matches the
# sealed proposal. The authoritative read-back already ran inside the use
# case; this layer must never declare success on a divergent view.
# ---------------------------------------------------------------------------


def verify(change: dict[str, Any], view: Any) -> dict[str, Any]:
    if view is None or view.diagnostic_id != change["diagnostic_id"]:
        _raise(
            "Read model divergiu do diagnostic proposto.",
            code=OUTCOME_VERIFICATION_FAILED,
            status_code=409,
        )
    action = change["action"]
    payload = dict(change.get("payload") or {})
    ok = _verify_action(view, action, payload, change)
    if not ok:
        _raise(
            "Postcondition divergiu do estado retornado.",
            code=OUTCOME_VERIFICATION_FAILED,
            status_code=409,
        )
    return {"diagnostic": asdict(view), "action": action}


def _verify_action(view, action: str, payload: dict, change: dict) -> bool:
    if action == "create":
        return (
            view.revision_id == change["revision_id"]
            and view.problem_statement.text
            == str(change["problem_statement"]).strip()
        )
    if action == "add_finding":
        return any(f.finding_id == payload["finding_id"] for f in view.findings)
    if action == "add_hypothesis":
        return any(
            h.hypothesis_id == payload["hypothesis_id"]
            for h in view.hypotheses
        )
    if action == "add_causal_link":
        return any(l.link_id == payload["link_id"] for l in view.causal_links)
    if action == "add_evidence_link":
        return any(
            l.link_id == payload["link_id"] for l in view.evidence_links
        )
    if action == "add_conclusion":
        return any(
            c.conclusion_id == payload["conclusion_id"]
            for c in view.diagnostic_conclusions
        )
    if action in HYPOTHESIS_LIFECYCLE_ACTIONS:
        hyp = _find(view.hypotheses, "hypothesis_id", payload["hypothesis_id"])
        target = {
            "validate_hypothesis": "VALIDATED",
            "reject_hypothesis": "REJECTED",
            "supersede_hypothesis": "SUPERSEDED",
        }[action]
        return hyp is not None and hyp.lifecycle.value == target
    if action in HYPOTHESIS_MARK_ACTIONS:
        hyp = _find(view.hypotheses, "hypothesis_id", payload["hypothesis_id"])
        target = {
            "mark_hypothesis_stale_evidence": "STALE_EVIDENCE",
            "mark_hypothesis_revalidation_required": "REVALIDATION_REQUIRED",
        }[action]
        return hyp is not None and hyp.effective_validation.value == target
    concl = _find(
        view.diagnostic_conclusions, "conclusion_id", payload["conclusion_id"]
    )
    target = {
        "validate_conclusion": "VALIDATED",
        "reject_conclusion": "REJECTED",
        "supersede_conclusion": "SUPERSEDED",
    }[action]
    return concl is not None and concl.lifecycle.value == target


def _find(items, key: str, value: str):
    for item in items:
        if getattr(item, key, None) == value:
            return item
    return None
