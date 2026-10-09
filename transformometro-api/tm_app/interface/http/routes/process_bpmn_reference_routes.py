"""Process ↔ BPMN Modeler explicit reference (G5).

Narrow capability surface — NOT a generic BPMN proxy:
- read/replace/remove the Transformômetro-owned reference;
- list picker candidates (models/revisions) with user-delegated auth.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_process_bpmn_reference import (
    BpmnDependencyUnavailable,
    DualModeConflict,
    ProcessBpmnReferenceUseCases,
)
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.gateways.bpmn_modeler_gateway import (
    BpmnModelerGateway,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_document_repository import (
    ProcessBpmnDocumentRepository,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_reference_repository import (
    ProcessBpmnReferenceRepository,
)
from tm_app.interface.http.routes.crud_routes import _audit

router = APIRouter(
    prefix="/transformometro", tags=["Transformômetro — referência BPMN"]
)
_use_cases = ProcessBpmnReferenceUseCases(
    ProcessBpmnReferenceRepository(),
    BpmnModelerGateway(),
    docs=ProcessBpmnDocumentRepository(),
)


class ProcessBpmnReferenceBody(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=64)
    revision_number: int = Field(..., gt=0)


def _handle(exc: Exception):
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, DualModeConflict):
        return fail(str(exc), 409, {"error_kind": "dual_mode_forbidden"})
    if isinstance(exc, BpmnDependencyUnavailable):
        return fail(
            str(exc),
            exc.status_code,
            {"error_kind": "dependency_unavailable", "integration": "bpmn-modeler"},
        )
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, RuntimeError) and str(exc) == "OUTCOME_VERIFICATION_FAILED":
        return fail("A gravação não confirmou o estado esperado.", 409)
    raise exc


def _authorization(request: Request) -> str:
    return request.headers.get("authorization") or ""


def _ref_payload(ref: dict | None) -> dict | None:
    if not ref:
        return None
    return {
        "model_id": ref.get("model_id"),
        "revision_number": ref.get("revision_number"),
    }


@router.get(
    "/processos/{processo_id}/bpmn-reference",
    operation_id="get_process_bpmn_reference",
)
def get_process_bpmn_reference(request: Request, processo_id: str):
    try:
        result = _use_cases.get_reference(
            request.state.user,
            processo_id,
            authorization=_authorization(request),
        )
        return ok(result, "Referência BPMN do processo.")
    except Exception as exc:
        return _handle(exc)


@router.put(
    "/processos/{processo_id}/bpmn-reference",
    operation_id="set_process_bpmn_reference",
)
def set_process_bpmn_reference(
    request: Request, processo_id: str, body: ProcessBpmnReferenceBody
):
    try:
        result = _use_cases.set_reference(
            request.state.user,
            processo_id,
            model_id=body.model_id,
            revision_number=body.revision_number,
            authorization=_authorization(request),
        )
        previous = result.pop("previous", None)
        _audit(
            request,
            "processo_bpmn_reference",
            processo_id,
            "update" if previous else "create",
            {
                "old_reference": _ref_payload(previous),
                "new_reference": _ref_payload(result.get("reference")),
            },
        )
        return ok(result, "Modelo BPMN vinculado ao processo.")
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/processos/{processo_id}/bpmn-reference",
    operation_id="remove_process_bpmn_reference",
)
def remove_process_bpmn_reference(request: Request, processo_id: str):
    try:
        result = _use_cases.remove_reference(request.state.user, processo_id)
        _audit(
            request,
            "processo_bpmn_reference",
            processo_id,
            "delete",
            {
                "old_reference": _ref_payload(result.get("removed")),
                "new_reference": None,
            },
        )
        return ok(
            {"reference": None},
            "Referência BPMN desvinculada. O modelo BPMN não foi alterado.",
        )
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-reference/candidates",
    operation_id="list_process_bpmn_model_candidates",
)
def list_process_bpmn_model_candidates(request: Request, processo_id: str):
    try:
        result = _use_cases.list_model_candidates(
            request.state.user,
            processo_id,
            authorization=_authorization(request),
        )
        return ok(result, "Modelos BPMN disponíveis.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-reference/candidates/{model_id}/revisions",
    operation_id="list_process_bpmn_model_revisions",
)
def list_process_bpmn_model_revisions(
    request: Request, processo_id: str, model_id: str
):
    try:
        result = _use_cases.list_model_revisions(
            request.state.user,
            processo_id,
            model_id,
            authorization=_authorization(request),
        )
        return ok(result, "Revisões do modelo BPMN.")
    except Exception as exc:
        return _handle(exc)
