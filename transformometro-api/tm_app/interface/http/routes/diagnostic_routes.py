"""Portal HTTP surface for Diagnostic — canonical READ + governed WRITE.

This module is an ADAPTER only:

    READ    → canonical Application use cases (ListDiagnosticsByRevision,
              GetDiagnostic) — no SQL, no repository-shaped responses.
    PREPARE → canonical GovernedWriteOrchestrator (create_diagnostic /
              manage_diagnostic capabilities) — seals an opaque proposal;
              NEVER writes the aggregate.
    COMMIT  → canonical GovernedActionsFacade.commit_proposal — the same
              confirmation/fingerprint/actor-binding/stale-detection path
              used by GPT Actions and MCP. No second confirmation flow.

Boundary-owned concerns enforced here (and only here):
    - new technical ids (diagnostic_id, finding_id, hypothesis_id, link_id,
      conclusion_id) are generated server-side — caller-supplied ids are
      rejected;
    - provenance is forced to ``USER`` — a Portal caller can never mint a
      TEO/other origin;
    - ``confirmation=true`` is required to commit a proposal.

Realtime: exactly one ``entity.updated`` (entityType=diagnostic,
sectionKey=diagnostico, payload={revision_id}) is emitted AFTER the ACT is
verified — never on PREPARE, never on failed/unverified ACT.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from tm_app.application.governed_writes.diagnostic_capabilities import (
    CREATE_CAPABILITY,
    DIAGNOSTIC_CAPABILITIES,
    MANAGE_ACTIONS,
    MANAGE_CAPABILITY,
    SERVER_GENERATED_ID_FIELD,
    require_prepare_authz,
)
from tm_app.application.governed_writes.errors import (
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
)
from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.services.transformometro_realtime_notify import (
    notify_entity_updated,
)
from tm_app.application.use_cases.diagnostic_read import (
    DiagnosticReadError,
    GetDiagnostic,
    ListDiagnosticsByRevision,
)
from tm_app.core.auth_actor import actor_from_request, client_id_from_request
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.diagnostic_composition import (
    build_diagnostic_write_stack,
)
from tm_app.interface.diagnostic_projection import (
    project_read_context,
    project_revision,
    project_summary,
)

router = APIRouter(
    prefix="/transformometro",
    tags=["Transformômetro — diagnóstico"],
)
logger = logging.getLogger(__name__)

# One canonical Diagnostic composition shared by reads AND governed writes —
# no second repository/read authority for the Portal surface.
_diagnostic_stack = build_diagnostic_write_stack()
_dispatch = GptActionsDispatchService()
_orchestrator = GovernedWriteOrchestrator(
    _dispatch,
    GuidedImprovementPackageService(_dispatch),
    diagnostic_stack=_diagnostic_stack,
)
_governed = GovernedActionsFacade(_orchestrator, _dispatch)

# Additive actions whose entity payload carries provenance — the Portal
# always writes ProvenanceOrigin.USER into the sealed change.
_PROVENANCE_ACTIONS = frozenset(
    {"add_finding", "add_hypothesis", "add_conclusion"}
)


class DiagnosticCreatePrepareBody(BaseModel):
    """Caller provides only the business statement; ids are server-owned."""

    model_config = ConfigDict(extra="forbid")

    problem_statement: str = Field(min_length=1)


class DiagnosticManagePrepareBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class GovernedProposalCommitBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_handle: str = Field(min_length=1)
    confirmation: bool


def _handle(exc: Exception):
    if isinstance(exc, GovernedWriteError):
        data = dict(exc.data or {})
        data.setdefault("error_code", exc.code)
        status = exc.status_code
        if exc.code == VALIDATION and status == 400:
            # Portal error contract: malformed business input → 422.
            status = 422
        return fail(exc.message, status, data=data)
    if isinstance(exc, DiagnosticReadError):
        status = 400
        if exc.code in (
            "diagnostic.not_found",
            "diagnostic.revision_not_found",
        ):
            status = 404
        elif exc.code == "diagnostic.read_integrity_error":
            status = 409
        return fail(str(exc), status, data={"error_code": exc.code})
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    raise exc


def _portal_provenance(provided) -> dict:
    """Force ProvenanceOrigin.USER — caller can never mint TEO/other origin."""
    if provided is not None:
        if not isinstance(provided, dict):
            raise GovernedWriteError(
                "provenance deve ser objeto {origin, detail?}.",
                code=VALIDATION,
                status_code=422,
            )
        origin = str(provided.get("origin") or "").strip().upper()
        if origin not in ("", "USER"):
            raise GovernedWriteError(
                "provenance.origin é imposta pelo servidor (USER) e não "
                "pode ser sobrescrita.",
                code=VALIDATION,
                status_code=422,
            )
        detail = provided.get("detail")
        if detail is not None:
            return {"origin": "USER", "detail": str(detail)}
    return {"origin": "USER"}


def _notify_diagnostic_commit(request: Request, result: dict) -> None:
    """Invalidation signal only — emitted AFTER verified ACT, never before.

    Payload is data-minimized by contract: only ``revision_id`` (the scope
    key authorized for the Diagnostic realtime contract). No
    claim/finding/conclusion/evidence content.
    """
    capability = result.get("capability")
    if capability not in DIAGNOSTIC_CAPABILITIES:
        return
    diagnostic = (result.get("data") or {}).get("diagnostic") or {}
    diagnostic_id = str(diagnostic.get("diagnostic_id") or "").strip()
    revision_id = str(diagnostic.get("revision_id") or "").strip()
    if not diagnostic_id or not revision_id:
        return
    user_id, _, _ = actor_from_request(request)
    notify_entity_updated(
        entity_type="diagnostic",
        entity_id=diagnostic_id,
        action=("create" if capability == CREATE_CAPABILITY else "update"),
        actor_user_id=user_id,
        actor_client_id=client_id_from_request(request),
        payload={"revision_id": revision_id},
    )


@router.get(
    "/revisions/{revision_id}/diagnostics",
    operation_id="list_diagnostics_by_revision",
    summary="List revision-scoped Diagnostic summaries (canonical read)",
)
def list_diagnostics(request: Request, revision_id: str):
    try:
        # Canonical end-user gate: authenticated, principal_type==user,
        # transformometro.access — service principals are denied, fail closed.
        require_prepare_authz(request)
        result = ListDiagnosticsByRevision(
            _diagnostic_stack.diagnostics,
            _diagnostic_stack.revisions,
        ).execute(str(revision_id))
        return ok(
            {
                "revision": project_revision(result.revision),
                "items": [project_summary(item) for item in result.items],
                "total": len(result.items),
            },
            "Diagnostics da revisão.",
        )
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/diagnostics/{diagnostic_id}",
    operation_id="get_diagnostic",
    summary="Load one Diagnostic with revision context (canonical read)",
)
def get_diagnostic(request: Request, diagnostic_id: str):
    try:
        require_prepare_authz(request)
        ctx = GetDiagnostic(
            _diagnostic_stack.diagnostics,
            _diagnostic_stack.revisions,
            _diagnostic_stack.evidence,
        ).execute(str(diagnostic_id))
        return ok(project_read_context(ctx), "Diagnostic carregado.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/revisions/{revision_id}/diagnostics/prepare",
    operation_id="prepare_create_diagnostic",
    summary="PREPARE governed Diagnostic creation (no write)",
)
def prepare_create_diagnostic(
    request: Request,
    revision_id: str,
    body: DiagnosticCreatePrepareBody,
):
    try:
        # Explicit boundary guard: authenticated end-user + transformometro.access.
        # The orchestrator re-checks at PREPARE and ACT runs fresh Core AuthZ.
        require_prepare_authz(request)
        public = _orchestrator.prepare(
            request,
            capability=CREATE_CAPABILITY,
            args={
                "diagnostic_id": str(uuid4()),
                "revision_id": str(revision_id),
                "problem_statement": body.problem_statement,
                "provenance": {"origin": "USER"},
            },
        )
        return ok(
            public,
            "Proposta pronta — confirme via /governed-proposals/commit.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/diagnostics/{diagnostic_id}/prepare",
    operation_id="prepare_manage_diagnostic",
    summary="PREPARE one closed-list Diagnostic mutation (no write)",
)
def prepare_manage_diagnostic(
    request: Request,
    diagnostic_id: str,
    body: DiagnosticManagePrepareBody,
):
    try:
        require_prepare_authz(request)
        action = str(body.action or "").strip()
        if action not in MANAGE_ACTIONS:
            return fail(
                f"Action '{action}' não é uma mutation Diagnostic permitida.",
                422,
                data={
                    "error_code": "unsupported_action",
                    "allowed": sorted(MANAGE_ACTIONS),
                },
            )
        payload = dict(body.payload or {})
        id_field = SERVER_GENERATED_ID_FIELD.get(action)
        if id_field is not None:
            if id_field in payload:
                return fail(
                    f"'{id_field}' é gerado pelo servidor para a action "
                    f"'{action}' e não pode ser fornecido pelo caller.",
                    422,
                    data={"error_code": "server_owned_field", "field": id_field},
                )
            payload[id_field] = str(uuid4())
        if action in _PROVENANCE_ACTIONS:
            payload["provenance"] = _portal_provenance(payload.get("provenance"))
        public = _orchestrator.prepare(
            request,
            capability=MANAGE_CAPABILITY,
            args={
                "diagnostic_id": str(diagnostic_id),
                "action": action,
                "payload": payload,
            },
        )
        return ok(
            public,
            "Proposta pronta — confirme via /governed-proposals/commit.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/governed-proposals/commit",
    operation_id="commit_governed_proposal",
    summary="COMMIT opaque proposal_handle after explicit confirmation",
)
def commit_governed_proposal(
    request: Request,
    body: GovernedProposalCommitBody,
):
    try:
        # Explicit boundary guard — confirmation below is NOT authorization;
        # the canonical ACT path still runs fresh Core AuthZ (force_refresh).
        require_prepare_authz(request)
        if body.confirmation is not True:
            return fail(
                "confirmation=true é obrigatório para commitar uma proposta. "
                "Confirmação não é AuthZ — o backend revalida no ACT.",
                422,
                data={"error_code": "CONFIRMATION_REQUIRED"},
            )
        result = _governed.commit_proposal(
            request,
            proposal_handle=body.proposal_handle,
            confirmation=True,
        )
        # Realtime fires only here — WRITE + read-back + postcondition all
        # verified by the canonical governed path before this line runs.
        _notify_diagnostic_commit(request, result)
        return ok(result, "Proposta confirmada e verificada.")
    except Exception as exc:
        return _handle(exc)
