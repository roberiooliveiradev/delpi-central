"""P2-Upload SLICE-1 — evidências documentais (U1–U4).

`POST/GET /closing/competences/{period}/documents*` — mesmo envelope e
mapeamento de erros dos contratos P2-READ. Upload cria evidência
`ATTACHED` — nunca `VALIDATED`/`ACCEPTED`; o item do snapshot permanece
`EXPECTED`. Download é stream autenticado auditado (`DOCUMENT_DOWNLOADED`
registra a decisão de autorização, não a entrega) — sem URL pública, sem
vazamento de storage_key.

Resource scope (doc 103 §92/§166): `branch_scope` declara o filial-
contexto do request (MATRIX|BRANCH|BOTH, default BOTH); o documento herda
o escopo do item (competência = BOTH). Recurso fora do contexto é 404 —
`access` sozinho não alcança recurso fora do escopo declarado.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

from controllership_finance_app.application.services.closing_document_service import (
    ClosingDocumentService,
)
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    FileTooLarge,
)
from controllership_finance_app.domain.closing_documents.file_validation import (
    MAX_FILE_BYTES,
)
from controllership_finance_app.interface.http.authz import (
    actor_subject,
    authorized_user,
)

router = APIRouter(prefix="/closing/competences", tags=["Closing Documents"])

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
_CHUNK = 1024 * 1024


def _service() -> ClosingDocumentService:
    return ClosingDocumentService()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _document_view(row: dict) -> dict:
    """Contrato público do documento — nunca expõe storage físico."""
    return {
        "document_id": str(row["document_id"]),
        "competence_id": str(row["competence_id"]),
        "link_kind": row["link_kind"],
        "snapshot_item_id": (
            str(row["snapshot_item_id"]) if row["snapshot_item_id"] else None
        ),
        "snapshot_item_key": row.get("snapshot_item_key"),
        "branch_scope": row.get("branch_scope") or "BOTH",
        "title": row["title"],
        "attachment_role": row["attachment_role"],
        "state": row["state"],
        "current_version_no": row["current_version_no"],
        "uploaded_by": str(row["uploaded_by"]),
        "created_at": row["created_at"].isoformat()
        if row["created_at"]
        else None,
        "updated_at": row["updated_at"].isoformat()
        if row.get("updated_at")
        else None,
        "original_name": row.get("original_name"),
        "mime_type": row.get("mime_type"),
        "size_bytes": row.get("size_bytes"),
        "checksum_sha256": row.get("checksum_sha256"),
    }


async def _read_chunks_limited(file: UploadFile) -> list[bytes]:
    """Lê o multipart com cap mid-stream — aborta ao exceder 25 MB."""
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(_CHUNK):
        size += len(chunk)
        if size > MAX_FILE_BYTES:
            raise FileTooLarge("O arquivo excede o limite de 25 MB.")
        chunks.append(chunk)
    return chunks


@router.post(
    "/{period}/documents",
    operation_id="upload_competence_document",
    status_code=201,
)
async def upload_competence_document(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    file: UploadFile = File(...),
    idempotency_key: str = Form(...),
    snapshot_item_id: str | None = Form(default=None),
    title: str | None = Form(default=None),
    attachment_role: str | None = Form(default=None),
    branch_scope: str | None = Form(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U1 — D-U7=A: `idempotency_key` obrigatória no body (multipart form),
    `UNIQUE(competence_id, key)`+`request_hash`; replay retorna o original."""
    user = authorized_user(request)
    try:
        actor = actor_subject(user)
        chunks = await _read_chunks_limited(file)
        if snapshot_item_id:
            snapshot_item_id = str(uuid.UUID(snapshot_item_id))
        document, created = _service().upload(
            period=period,
            actor=actor,
            original_name=file.filename or "evidencia",
            declared_mime=file.content_type,
            chunks=chunks,
            snapshot_item_id=snapshot_item_id,
            title=title,
            attachment_role=attachment_role,
            idempotency_key=idempotency_key,
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "upload_competence_document")
    except (TypeError, ValueError):
        return _domain_fail(
            _invalid_item(), "upload_competence_document"
        )
    data = _document_view(document)
    if not created:
        data["deduplicated"] = True
    return ok(
        data,
        message=(
            "Documento anexado."
            if created
            else "Documento já registrado para esta chave de idempotência."
        ),
        status_code=201 if created else 200,
        operation_id="upload_competence_document",
    )


def _invalid_item() -> ChecklistDomainError:
    from controllership_finance_app.domain.closing_checklist.errors import (
        InvalidUpload,
    )

    return InvalidUpload("snapshot_item_id deve ser um UUID válido.")


@router.get(
    "/{period}/documents",
    operation_id="list_competence_documents",
)
def list_competence_documents(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    snapshot_item_id: str | None = Query(default=None),
    link_kind: str | None = Query(
        default=None, pattern="^(competence|competence_item)$"
    ),
    state: str | None = Query(
        default=None, pattern="^(ATTACHED|SUPERSEDED|CANCELLED)$"
    ),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """U2 — competência do path × filial-contexto declarado (resource
    scope): fora do escopo nunca é retornado (sem vazamento)."""
    authorized_user(request)
    try:
        result = _service().list_documents(
            period=period,
            snapshot_item_id=snapshot_item_id,
            link_kind=link_kind,
            state=state,
            branch_scope=branch_scope,
            limit=limit,
            offset=offset,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_competence_documents")
    return ok(
        {
            "documents": [_document_view(r) for r in result["items"]],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
        },
        operation_id="list_competence_documents",
    )


@router.get(
    "/{period}/documents/{document_id}",
    operation_id="get_competence_document",
)
def get_competence_document(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U3 — metadados do documento; associação documento↔competência
    sempre validada (cross-competence = 404) e escopo de filial do
    request aplicado (cross-branch = 404)."""
    authorized_user(request)
    try:
        row = _service().get_document(
            period=period,
            document_id=str(document_id),
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_competence_document")
    return ok(_document_view(row), operation_id="get_competence_document")


@router.get(
    "/{period}/documents/{document_id}/versions/{version_no}/content",
    operation_id="download_document_version",
)
def download_document_version(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    version_no: int = Path(ge=1),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U4 — stream autenticado; `DOCUMENT_DOWNLOADED` registra a decisão
    de autorização (AUTHORIZED/DENIED/FAILED com `phase`), nunca a
    entrega concluída — `FileResponse` não prova transmissão (D-U3=A)."""
    user = authorized_user(request)
    try:
        path, meta = _service().resolve_download(
            period=period,
            document_id=str(document_id),
            version_no=version_no,
            actor=actor_subject(user),
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "download_document_version")
    return FileResponse(
        path,
        media_type=meta["mime_type"],
        filename=meta["original_name"],
    )
