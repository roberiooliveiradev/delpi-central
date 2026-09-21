from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_process_documents import ProcessDocumentUseCases
from tm_app.core.responses import fail, ok
from tm_app.domain.services.process_document_rules import (
    MAX_CONTENT_MD_LENGTH,
    MAX_TITLE_LENGTH,
)
from tm_app.infrastructure.persistence.repositories.process_document_repository import (
    ProcessDocumentRepository,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro — documentação do processo"])
_docs = ProcessDocumentUseCases(ProcessDocumentRepository())


class ProcessDocumentCreateBody(BaseModel):
    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    content_md: str = Field(default="", max_length=MAX_CONTENT_MD_LENGTH)


class ProcessDocumentUpdateBody(BaseModel):
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    content_md: str | None = Field(default=None, max_length=MAX_CONTENT_MD_LENGTH)


def _handle(exc: Exception):
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, RuntimeError) and str(exc) == "OUTCOME_VERIFICATION_FAILED":
        return fail("A gravação não confirmou o estado esperado.", 409)
    raise exc


@router.get(
    "/processos/{processo_id}/documents",
    operation_id="list_process_documents",
)
def list_process_documents(request: Request, processo_id: str):
    try:
        items = _docs.list_documents(request.state.user, processo_id)
        return ok(
            {
                "total": len(items),
                "items": [item.to_summary_dict() for item in items],
            },
            "Documentação do processo.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/processos/{processo_id}/documents",
    operation_id="create_process_document",
)
def create_process_document(request: Request, processo_id: str, body: ProcessDocumentCreateBody):
    try:
        created = _docs.create_document(
            request.state.user,
            processo_id,
            title=body.title,
            content_md=body.content_md,
        )
        return ok(created.to_dict(), "Documento criado.", 201)
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processos/{processo_id}/documents/{document_id}",
    operation_id="get_process_document",
)
def get_process_document(request: Request, processo_id: str, document_id: str):
    try:
        doc = _docs.get_document(request.state.user, processo_id, document_id)
        return ok(doc.to_dict(), "Documento do processo.")
    except Exception as exc:
        return _handle(exc)


@router.patch(
    "/processos/{processo_id}/documents/{document_id}",
    operation_id="update_process_document",
)
def update_process_document(
    request: Request,
    processo_id: str,
    document_id: str,
    body: ProcessDocumentUpdateBody,
):
    try:
        updated = _docs.update_document(
            request.state.user,
            processo_id,
            document_id,
            title=body.title,
            content_md=body.content_md,
        )
        return ok(updated.to_dict(), "Documento atualizado.")
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/processos/{processo_id}/documents/{document_id}",
    operation_id="delete_process_document",
)
def delete_process_document(request: Request, processo_id: str, document_id: str):
    try:
        deleted = _docs.delete_document(request.state.user, processo_id, document_id)
        return ok(deleted.to_summary_dict(), "Documento excluído.")
    except Exception as exc:
        return _handle(exc)
