"""Process-scoped native BPMN document (G7).

Superfície estreita por processo — NÃO é proxy genérico:
- working copy canônico com ETag "v<n>" + If-Match (mesma semântica do Modeler);
- revisões explícitas, imutáveis, append-only, com proveniência de restore;
- validação offline via shared/bpmn_validation (nunca delega ao Modeler).

XOR (ADR-006): documento nativo e referência externa (G5) não coexistem.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_process_bpmn_document import (
    DualModeConflict,
    ProcessBpmnDocumentUseCases,
    UnsafeArtifact,
    VersionConflict,
)
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.persistence.repositories.process_bpmn_document_repository import (
    ProcessBpmnDocumentRepository,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_reference_repository import (
    ProcessBpmnReferenceRepository,
)
from tm_app.interface.http.etag import format_etag, parse_if_match
from tm_app.interface.http.routes.crud_routes import _audit

router = APIRouter(
    prefix="/transformometro", tags=["Transformômetro — documento BPMN nativo"]
)
_use_cases = ProcessBpmnDocumentUseCases(
    ProcessBpmnDocumentRepository(), ProcessBpmnReferenceRepository()
)


class CreateRevisionBody(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class CreateDocumentBody(BaseModel):
    xml: str | None = None


def _handle(exc: Exception):
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, DualModeConflict):
        return fail(str(exc), 409, {"error_kind": "dual_mode_forbidden"})
    if isinstance(exc, VersionConflict):
        return fail(str(exc), 409, {"error_kind": "version_conflict"})
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, UnsafeArtifact):
        return fail(str(exc), 400, {"error_kind": "unsafe_artifact"})
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, RuntimeError) and str(exc) == "OUTCOME_VERIFICATION_FAILED":
        return fail("A gravação não confirmou o estado esperado.", 409)
    raise exc


def _require_if_match(request: Request) -> int:
    state, version = parse_if_match(request.headers.get("if-match"))
    if state == "missing":
        raise ValueError("O cabeçalho If-Match é obrigatório nesta operação.")
    if state == "malformed" or version is None:
        raise ValueError('Cabeçalho If-Match malformado; use "v<versão>".')
    return version


def _xml_response(content: str, headers: dict[str, str]) -> Response:
    return Response(
        content=content,
        media_type="application/xml",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            **headers,
        },
    )


def _actor_name(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return str(getattr(user, "name", "") or getattr(user, "email", "") or "")


async def _read_xml_body(request: Request) -> str | None:
    body = await request.body()
    if not body:
        return None
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip()
    if content_type == "application/json":
        import json

        payload = json.loads(body.decode("utf-8"))
        return payload.get("xml") if isinstance(payload, dict) else None
    return body.decode("utf-8")


@router.get(
    "/processos/{processo_id}/bpmn-document",
    operation_id="get_process_bpmn_document",
)
def get_process_bpmn_document(request: Request, processo_id: str):
    try:
        result = _use_cases.get_document(request.state.user, processo_id)
        response = ok(result, "Documento BPMN do processo.")
        response.headers["ETag"] = format_etag(result["version"])
        return response
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/processos/{processo_id}/bpmn-document",
    operation_id="create_process_bpmn_document",
    status_code=201,
)
async def create_process_bpmn_document(request: Request, processo_id: str):
    try:
        xml = await _read_xml_body(request)
        doc = _use_cases.create_document(request.state.user, processo_id, xml)
        _audit(
            request,
            "processo_bpmn_document",
            processo_id,
            "create",
            {"document_id": doc.id, "source": "import" if xml else "blank"},
        )
        return ok(doc.to_dict(), "Documento BPMN criado.", status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-document/working-copy",
    operation_id="get_process_bpmn_working_copy",
)
def get_process_bpmn_working_copy(request: Request, processo_id: str):
    try:
        result = _use_cases.get_working_copy(request.state.user, processo_id)
        response = ok(result, "Working copy BPMN.")
        response.headers["ETag"] = format_etag(result["version"])
        return response
    except Exception as exc:
        return _handle(exc)


@router.put(
    "/processos/{processo_id}/bpmn-document/working-copy",
    operation_id="save_process_bpmn_working_copy",
)
async def save_process_bpmn_working_copy(request: Request, processo_id: str):
    try:
        expected = _require_if_match(request)
        xml = await _read_xml_body(request)
        if xml is None:
            raise ValueError("Corpo XML obrigatório.")
        doc = _use_cases.save_working_copy(
            request.state.user,
            processo_id,
            xml=xml,
            expected_version=expected,
        )
        response = ok(doc.to_dict(), "Working copy salvo.")
        response.headers["ETag"] = format_etag(doc.version)
        return response
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/processos/{processo_id}/bpmn-document",
    operation_id="delete_process_bpmn_document",
)
def delete_process_bpmn_document(request: Request, processo_id: str):
    try:
        result = _use_cases.delete_document(request.state.user, processo_id)
        _audit(
            request,
            "processo_bpmn_document",
            processo_id,
            "delete",
            {"document_id": result.get("document_id")},
        )
        return ok(result, "Documento BPMN removido do processo.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-document/revisions",
    operation_id="list_process_bpmn_revisions",
)
def list_process_bpmn_revisions(request: Request, processo_id: str):
    try:
        result = _use_cases.list_revisions(request.state.user, processo_id)
        return ok(result, "Revisões do documento BPMN.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/processos/{processo_id}/bpmn-document/revisions",
    operation_id="create_process_bpmn_revision",
    status_code=201,
)
async def create_process_bpmn_revision(
    request: Request, processo_id: str, body: CreateRevisionBody | None = None
):
    try:
        expected = _require_if_match(request)
        rev = _use_cases.create_revision(
            request.state.user,
            processo_id,
            expected_version=expected,
            name=body.name if body else None,
            description=body.description if body else None,
        )
        _audit(
            request,
            "processo_bpmn_revision",
            processo_id,
            "create",
            {"revision_number": rev.revision_number, "name": rev.name},
        )
        return ok(rev.to_dict(), "Revisão criada.", status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-document/revisions/{revision_number}",
    operation_id="get_process_bpmn_revision",
)
def get_process_bpmn_revision(
    request: Request, processo_id: str, revision_number: int
):
    try:
        result = _use_cases.get_revision(
            request.state.user, processo_id, revision_number
        )
        return ok(result, "Revisão do documento BPMN.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-document/revisions/{revision_number}/export",
    operation_id="export_process_bpmn_revision",
)
def export_process_bpmn_revision(
    request: Request, processo_id: str, revision_number: int
):
    try:
        rev = _use_cases.export_revision_xml(
            request.state.user, processo_id, revision_number
        )
        return _xml_response(
            rev.artifact_xml or "",
            {
                "X-Artifact-SHA256": rev.artifact_sha256,
                "Content-Disposition": (
                    f'attachment; filename="processo-bpmn-r{revision_number}.bpmn"'
                ),
            },
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/processos/{processo_id}/bpmn-document/revisions/{revision_number}/restore",
    operation_id="restore_process_bpmn_revision",
)
async def restore_process_bpmn_revision(
    request: Request, processo_id: str, revision_number: int
):
    try:
        expected = _require_if_match(request)
        doc, rev = _use_cases.restore_revision(
            request.state.user,
            processo_id,
            revision_number,
            expected_version=expected,
        )
        _audit(
            request,
            "processo_bpmn_revision",
            processo_id,
            "restore",
            {
                "restored_revision": revision_number,
                "new_revision": rev.revision_number,
            },
        )
        response = ok(doc.to_dict(), "Revisão restaurada no working copy.")
        response.headers["ETag"] = format_etag(doc.version)
        return response
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/processos/{processo_id}/bpmn-document/working-copy/validate",
    operation_id="validate_process_bpmn_working_copy",
)
async def validate_process_bpmn_working_copy(request: Request, processo_id: str):
    try:
        candidate = await _read_xml_body(request)
        result = _use_cases.validate_working_copy(
            request.state.user, processo_id, candidate
        )
        return ok(result, "Validação do artefato BPMN.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/bpmn-document/working-copy/export",
    operation_id="export_process_bpmn_working_copy",
)
def export_process_bpmn_working_copy(request: Request, processo_id: str):
    try:
        doc = _use_cases.export_working_copy(request.state.user, processo_id)
        return _xml_response(
            doc.working_copy_xml,
            {
                "ETag": format_etag(doc.version),
                "X-Artifact-SHA256": doc.working_copy_sha256,
                "Content-Disposition": 'attachment; filename="processo-bpmn.bpmn"',
            },
        )
    except Exception as exc:
        return _handle(exc)
