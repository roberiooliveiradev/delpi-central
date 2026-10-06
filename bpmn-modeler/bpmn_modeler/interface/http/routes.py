from __future__ import annotations

import logging
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from bpmn_modeler.application.errors import (
    CONFLICT,
    INPUT_REJECTED_SECURITY,
    INVALID_DISPLAY_NAME,
    MODEL_ARCHIVED,
    MODEL_NOT_FOUND,
    NO_CHANGES,
    OUTCOME_VERIFICATION_FAILED,
    REVISION_NOT_FOUND,
    UNAUTHORIZED_OPERATION,
    VALIDATION_BLOCKED,
    ApplicationError,
)
from bpmn_modeler.application.use_cases import (
    ArtifactInput,
    BpmnModelerService,
    CallerIdentity,
)
from bpmn_modeler.infrastructure.validation.intake import (
    MAX_INPUT_BYTES,
    intake_bytes,
)

from .auth import CallerDep
from .etag import format_etag, parse_if_match
from .filenames import content_disposition, export_filename
from .responses import error_response, success_envelope
from .schemas import (
    CreateModelRequest,
    CreateRevisionRequest,
    DuplicateModelRequest,
    RenameModelRequest,
    issue_response,
    model_detail,
    model_summary,
    mutation_result,
    report_response,
    revision_summary,
    summary_record_to_response,
)

logger = logging.getLogger(__name__)

router = APIRouter()

PERM_VIEW = "bpmn-modeler.view"
PERM_EDIT = "bpmn-modeler.edit"
PERM_MANAGE = "bpmn-modeler.manage"

XML_MEDIA = "application/xml; charset=utf-8"


def get_service(request: Request) -> BpmnModelerService:
    return request.app.state.service


ServiceDep = Annotated[BpmnModelerService, Depends(get_service)]


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _parse_model_id(raw: str, request: Request) -> str:
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError):
        raise ApplicationError(MODEL_NOT_FOUND, "Modelo não encontrado.")


def _require_if_match(request: Request) -> int:
    status, version = parse_if_match(request.headers.get("if-match"))
    if status == "missing":
        raise ApplicationError(
            "PRECONDITION_REQUIRED",
            "O cabeçalho If-Match é obrigatório nesta operação.",
            {"required_header": "If-Match"},
        )
    if status == "malformed":
        raise ApplicationError(
            "INVALID_REQUEST",
            "Cabeçalho If-Match malformado; use \"v<versão>\".",
        )
    return version


def _require_xml_content_type(request: Request) -> None:
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip()
    if content_type != "application/xml":
        raise ApplicationError(
            "INVALID_REQUEST",
            "Content-Type deve ser application/xml; charset=utf-8.",
        )


async def _xml_artifact_input(request: Request) -> ArtifactInput:
    _require_xml_content_type(request)
    raw = await request.body()
    if len(raw) > MAX_INPUT_BYTES:
        raise ApplicationError("PAYLOAD_TOO_LARGE", "O arquivo excede o tamanho máximo.")
    intake = intake_bytes(raw)
    return ArtifactInput(artifact=intake.artifact, evidence=intake.evidence)


async def _upload_artifact_input(request: Request, file: UploadFile | None) -> ArtifactInput:
    raw = await file.read() if file is not None else b""
    if len(raw) > MAX_INPUT_BYTES:
        raise ApplicationError("PAYLOAD_TOO_LARGE", "O arquivo excede o tamanho máximo.")
    intake = intake_bytes(raw)
    return ArtifactInput(artifact=intake.artifact, evidence=intake.evidence)


def _mutation_response(outcome, request: Request, status: int = 200):
    return JSONResponse(
        status_code=status,
        content=success_envelope(
            mutation_result(outcome).model_dump(mode="json"),
            outcome.message,
        ),
        headers={
            "ETag": format_etag(outcome.version),
            "X-Artifact-SHA256": outcome.artifact_sha256 or "",
        },
    )


def _xml_response(content: str, headers: dict[str, str]) -> Response:
    return Response(
        content=content.encode("utf-8"),
        media_type="application/xml",
        headers={"Cache-Control": "no-store", **headers},
    )


# --------------------------------------------------------------------- #
# runtime support                                                        #
# --------------------------------------------------------------------- #

@router.get("/health", operation_id="health", openapi_extra={"x-required-permission": None})
async def health():
    return {"status": "ok"}


@router.get("/ready", operation_id="ready", openapi_extra={"x-required-permission": None})
async def ready(request: Request):
    checks = request.app.state.readiness()
    status = 200 if all(checks.values()) else 503
    return JSONResponse(
        status_code=status,
        content={
            "status": "ready" if status == 200 else "not_ready",
            "checks": checks,
        },
    )


# --------------------------------------------------------------------- #
# models                                                                 #
# --------------------------------------------------------------------- #

@router.get("/models", operation_id="listModels",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def list_models(
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
    query: str | None = Query(default=None, max_length=120),
    archived: Literal["active", "archived", "all"] = "active",
    sort: Literal["updated_at", "created_at", "display_name"] = "updated_at",
    direction: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    result = service.list_models(
        query=query,
        archived=archived,
        sort=sort,
        direction=direction,
        page=page,
        page_size=page_size,
        caller=caller,
    )
    return success_envelope(
        {
            "items": [
                summary_record_to_response(r).model_dump(mode="json")
                for r in result.items
            ],
            "page": result.page,
            "page_size": result.page_size,
            "has_more": result.has_more,
        }
    )


@router.post("/models", operation_id="createModel", status_code=201,
             openapi_extra={"x-required-permission": PERM_EDIT})
async def create_model(
    body: CreateModelRequest,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    outcome = service.create_model(body.display_name, caller)
    return _mutation_response(outcome, request, status=201)


@router.post("/models/import", operation_id="importModel", status_code=201,
             openapi_extra={"x-required-permission": PERM_EDIT})
async def import_model(
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
    file: UploadFile | None = File(default=None),
    display_name: str = Form(default=""),
):
    if file is None:
        raise ApplicationError("INVALID_REQUEST", "Campo 'file' é obrigatório.")
    raw = await _upload_artifact_input(request, file)
    outcome = service.import_model(raw, display_name, caller)
    return _mutation_response(outcome, request, status=201)


@router.post("/imports/inspect", operation_id="inspectImport",
             openapi_extra={"x-required-permission": PERM_EDIT})
async def inspect_import(
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
    file: UploadFile | None = File(default=None),
):
    if not caller.can(PERM_EDIT):
        raise ApplicationError(
            UNAUTHORIZED_OPERATION,
            "Permissão insuficiente para esta operação.",
            {"required_permission": PERM_EDIT},
        )
    if file is None:
        raise ApplicationError("INVALID_REQUEST", "Campo 'file' é obrigatório.")
    raw = await _upload_artifact_input(request, file)
    result = service.inspect_import(raw)
    return success_envelope(
        {
            "recognition_state": result.recognition_state.value,
            "eligible_to_import": result.eligible_to_import,
            "validation_report": (
                report_response(result.validation_report).model_dump(mode="json")
                if result.validation_report
                else None
            ),
            "artifact_byte_length": result.artifact_byte_length,
            "artifact_sha256": result.artifact_sha256,
        }
    )


@router.get("/models/{model_id}", operation_id="getModel",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def get_model(model_id: str, request: Request, service: ServiceDep, caller: CallerDep):
    model = service.get_model(_parse_model_id(model_id, request), caller)
    artifact_sha = None
    import hashlib
    artifact_sha = hashlib.sha256(
        model.working_copy.artifact.content.encode("utf-8")
    ).hexdigest()
    return JSONResponse(
        content=success_envelope(model_detail(model).model_dump(mode="json")),
        headers={
            "ETag": format_etag(model.version),
            "X-Artifact-SHA256": artifact_sha,
        },
    )


@router.patch("/models/{model_id}", operation_id="renameModel",
              openapi_extra={"x-required-permission": PERM_MANAGE})
async def rename_model(
    model_id: str,
    body: RenameModelRequest,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    expected = _require_if_match(request)
    outcome = service.rename_model(
        _parse_model_id(model_id, request), body.display_name, expected, caller
    )
    return _mutation_response(outcome, request)


@router.post("/models/{model_id}/duplicate", operation_id="duplicateModel",
             status_code=201, openapi_extra={"x-required-permission": PERM_MANAGE})
async def duplicate_model(
    model_id: str,
    body: DuplicateModelRequest,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    outcome = service.duplicate_model(
        _parse_model_id(model_id, request), body.display_name, caller
    )
    return _mutation_response(outcome, request, status=201)


@router.post("/models/{model_id}/archive", operation_id="archiveModel",
             openapi_extra={"x-required-permission": PERM_MANAGE})
async def archive_model(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    expected = _require_if_match(request)
    outcome = service.archive_model(
        _parse_model_id(model_id, request), expected, caller
    )
    return _mutation_response(outcome, request)


@router.post("/models/{model_id}/unarchive", operation_id="unarchiveModel",
             openapi_extra={"x-required-permission": PERM_MANAGE})
async def unarchive_model(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    expected = _require_if_match(request)
    outcome = service.unarchive_model(
        _parse_model_id(model_id, request), expected, caller
    )
    return _mutation_response(outcome, request)


# --------------------------------------------------------------------- #
# working copy                                                           #
# --------------------------------------------------------------------- #

@router.get("/models/{model_id}/working-copy", operation_id="getWorkingCopy",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def get_working_copy(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    read = service.get_working_copy(_parse_model_id(model_id, request), caller)
    return _xml_response(
        read.artifact.content,
        {
            "ETag": format_etag(read.version),
            "X-Artifact-SHA256": read.artifact_sha256,
        },
    )


@router.put("/models/{model_id}/working-copy", operation_id="saveWorkingCopy",
            openapi_extra={"x-required-permission": PERM_EDIT})
async def save_working_copy(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    expected = _require_if_match(request)
    raw = await _xml_artifact_input(request)
    outcome = service.save_working_copy(
        _parse_model_id(model_id, request), raw, expected, caller
    )
    return _mutation_response(outcome, request)


@router.post("/models/{model_id}/working-copy/validate",
             operation_id="validateWorkingCopy",
             openapi_extra={"x-required-permission": PERM_VIEW})
async def validate_working_copy(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    raw = await _xml_artifact_input(request)
    report = service.validate_working_copy(
        _parse_model_id(model_id, request), raw, caller
    )
    return success_envelope(report_response(report).model_dump(mode="json"))


@router.get("/models/{model_id}/working-copy/export",
            operation_id="exportWorkingCopy",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def export_working_copy(
    model_id: str, request: Request, service: ServiceDep, caller: CallerDep
):
    model_id = _parse_model_id(model_id, request)
    model = service.get_model(model_id, caller)
    read = service.get_working_copy(model_id, caller)
    filename = export_filename(model.display_name)
    return _xml_response(
        read.artifact.content,
        {
            "ETag": format_etag(read.version),
            "X-Artifact-SHA256": read.artifact_sha256,
            "Content-Disposition": content_disposition(filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


# --------------------------------------------------------------------- #
# revisions                                                              #
# --------------------------------------------------------------------- #

@router.get("/models/{model_id}/revisions", operation_id="listRevisions",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def list_revisions(
    model_id: str,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    result = service.list_revisions(
        _parse_model_id(model_id, request), page, page_size, caller
    )
    return success_envelope(
        {
            "items": [
                revision_summary(r).model_dump(mode="json") for r in result.items
            ],
            "page": result.page,
            "page_size": result.page_size,
            "has_more": result.has_more,
        }
    )


@router.post("/models/{model_id}/revisions", operation_id="createRevision",
             status_code=201, openapi_extra={"x-required-permission": PERM_MANAGE})
async def create_revision(
    model_id: str,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
    body: CreateRevisionRequest | None = None,
):
    expected = _require_if_match(request)
    outcome = service.create_revision(
        _parse_model_id(model_id, request),
        expected,
        caller,
        name=body.name if body else None,
        description=body.description if body else None,
    )
    return _mutation_response(outcome, request, status=201)


@router.get("/models/{model_id}/revisions/{revision_number}",
            operation_id="getRevision",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def get_revision(
    model_id: str,
    revision_number: int,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    revision = service.get_revision(
        _parse_model_id(model_id, request), revision_number, caller
    )
    return success_envelope(revision_summary(revision).model_dump(mode="json"))


@router.post("/models/{model_id}/revisions/{revision_number}/restore",
             operation_id="restoreRevision",
             openapi_extra={"x-required-permission": PERM_MANAGE})
async def restore_revision(
    model_id: str,
    revision_number: int,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    expected = _require_if_match(request)
    outcome = service.restore_revision(
        _parse_model_id(model_id, request), revision_number, expected, caller
    )
    return _mutation_response(outcome, request)


@router.get("/models/{model_id}/revisions/{revision_number}/export",
            operation_id="exportRevision",
            openapi_extra={"x-required-permission": PERM_VIEW})
async def export_revision(
    model_id: str,
    revision_number: int,
    request: Request,
    service: ServiceDep,
    caller: CallerDep,
):
    model_id = _parse_model_id(model_id, request)
    model = service.get_model(model_id, caller)
    revision = service.get_revision(model_id, revision_number, caller)
    filename = export_filename(
        model.display_name, revision_number=revision.revision_number
    )
    return _xml_response(
        revision.artifact.content,
        {
            "X-Artifact-SHA256": revision.checksum,
            "Content-Disposition": content_disposition(filename),
            "X-Content-Type-Options": "nosniff",
        },
    )
