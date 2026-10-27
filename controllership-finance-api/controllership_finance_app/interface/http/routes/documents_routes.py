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
from pydantic import BaseModel, Field

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
    MANAGE_PERMISSION,
    actor_subject,
    authorized_user,
)
from delpi_auth.authz_core import has_permission

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
        "revision": row["revision"],
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


# -- SLICE-2: U5 substituição · U6 versões · U7 cancel · U8 eventos ---------------


def _version_view(row: dict) -> dict:
    """Contrato público da versão — metadados + referência estável,
    nunca storage_key nem caminho físico (doc 103 §6)."""
    return {
        "document_version_id": str(row["document_version_id"]),
        "document_id": str(row["document_id"]),
        "version_no": row["version_no"],
        "state": row["state"],
        "uploaded_by": str(row["uploaded_by"]),
        "created_at": row["created_at"].isoformat()
        if row["created_at"]
        else None,
        "original_name": row["original_name"],
        "mime_type": row["mime_type"],
        "size_bytes": row["size_bytes"],
        "checksum_sha256": row["checksum_sha256"],
    }


def _event_view(row: dict) -> dict:
    """Contrato público do evento de auditoria — sem tokens, caminhos
    físicos ou dados de autenticação (detail já é sanitized na escrita)."""
    return {
        "event_id": str(row["event_id"]),
        "event_type": row["event_type"],
        "actor_subject": str(row["actor_subject"]),
        "detail": row["detail"] or {},
        "created_at": row["created_at"].isoformat()
        if row["created_at"]
        else None,
    }


def _can_manage(request: Request):
    """`access` efetivo primeiro (rotas do portal), depois flag `manage`
    — D-U1=A: elegível = uploader OU `manage`, sempre com `access`."""
    user = authorized_user(request)
    return user, has_permission(user, MANAGE_PERMISSION)


@router.post(
    "/{period}/documents/{document_id}/versions",
    operation_id="replace_document_version",
    status_code=201,
)
async def replace_document_version(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    file: UploadFile = File(...),
    revision: int = Form(..., ge=1),
    idempotency_key: str = Form(...),
    branch_scope: str | None = Form(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U5 — substituição governada: `access` + scope + uploader-or-manage
    + business_rule + OCC `revision` + D-U7=A na mutação
    (`UNIQUE(document_id, idempotency_key)` + `request_hash`; replay
    idêntico retorna o documento com `deduplicated`, divergente 409).
    A versão anterior fica `SUPERSEDED` derivada — linha imutável."""
    user, can_manage = _can_manage(request)
    try:
        chunks = await _read_chunks_limited(file)
        document, created = _service().replace_document(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            can_manage=can_manage,
            original_name=file.filename or "evidencia",
            declared_mime=file.content_type,
            chunks=chunks,
            expected_revision=revision,
            idempotency_key=idempotency_key,
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "replace_document_version")
    data = _document_view(document)
    if not created:
        data["deduplicated"] = True
    return ok(
        data,
        message=(
            "Documento substituído. A versão anterior foi preservada."
            if created
            else "Substituição já registrada para esta chave "
            "de idempotência."
        ),
        status_code=201 if created else 200,
        operation_id="replace_document_version",
    )


@router.get(
    "/{period}/documents/{document_id}/versions",
    operation_id="list_document_versions",
)
def list_document_versions(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U6 — histórico imutável de versões; downloads seguem U4 com a
    mesma autorização (versão anterior continua acessível)."""
    authorized_user(request)
    try:
        rows = _service().list_document_versions(
            period=period,
            document_id=str(document_id),
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_document_versions")
    return ok(
        {"versions": [_version_view(r) for r in rows]},
        operation_id="list_document_versions",
    )


class CancelDocumentRequest(BaseModel):
    revision: int = Field(ge=1)


@router.post(
    "/{period}/documents/{document_id}/cancel",
    operation_id="cancel_document",
)
def cancel_document(
    request: Request,
    body: CancelDocumentRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U7 — cancelamento lógico (`CANCELLED != DELETED`): sai da
    listagem ativa, arquivos/versões/auditoria permanecem íntegros.
    Mesma autorização de U5 (uploader ou `manage` elegível) + OCC."""
    user, can_manage = _can_manage(request)
    try:
        document = _service().cancel_document(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            can_manage=can_manage,
            expected_revision=body.revision,
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "cancel_document")
    return ok(
        _document_view(document),
        message="Documento cancelado. O histórico foi preservado.",
        operation_id="cancel_document",
    )


@router.get(
    "/{period}/documents/{document_id}/events",
    operation_id="list_document_audit",
)
def list_document_audit(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """U8 — eventos de auditoria do documento (append-only): apenas os
    tipos documentais do contrato, escopo da competência e do
    filial-contexto declarado."""
    authorized_user(request)
    try:
        result = _service().list_document_events(
            period=period,
            document_id=str(document_id),
            branch_scope=branch_scope,
            limit=limit,
            offset=offset,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_document_audit")
    return ok(
        {
            "events": [_event_view(r) for r in result["items"]],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
        },
        operation_id="list_document_audit",
    )


# -- SLICE-3: U9 conversa documental ---------------------------------------------


def _message_view(row: dict, *, mine: bool | None = None) -> dict:
    """Contrato público da mensagem — sem `idempotency_key`/`request_hash`
    (mecanismo interno) e sem dados de autenticação. `author_name` é o
    snapshot resolvido no envio; NULL → a UI mostra identificação neutra
    (nunca o UUID como nome)."""
    view = {
        "message_id": str(row["message_id"]),
        "document_id": str(row["document_id"]),
        "competence_id": str(row["competence_id"]),
        "version_no": row["version_no"],
        "audience": row["audience"],
        "body": row["body"],
        "author_subject": str(row["author_subject"]),
        "author_name": row.get("author_name"),
        "created_at": row["created_at"].isoformat()
        if row["created_at"]
        else None,
    }
    if mine is not None:
        view["mine"] = mine
    return view


def _author_name(user) -> str | None:
    """Nome de exibição do ator autenticado (claim `name` do middleware).
    Sem fallback para e-mail/UUID — ausência fica NULL e a UI resolve a
    identificação neutra, sem inventar identidade."""
    name = (getattr(user, "name", None) or "").strip()
    return name if name and "@" not in name else None


class PostMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=128)


@router.get(
    "/{period}/documents/{document_id}/messages",
    operation_id="list_document_messages",
)
def list_document_messages(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """U9 — conversa do documento: cronológica, delimitada à competência
    do path e ao filial-contexto declarado (cross = 404). `mine` é
    derivado do ator autenticado pelo backend."""
    user = authorized_user(request)
    try:
        result = _service().list_document_messages(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            branch_scope=branch_scope,
            limit=limit,
            offset=offset,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_document_messages")
    return ok(
        {
            "messages": [
                _message_view(r, mine=r.get("mine"))
                for r in result["items"]
            ],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
        },
        operation_id="list_document_messages",
    )


@router.post(
    "/{period}/documents/{document_id}/messages",
    operation_id="post_document_message",
    status_code=201,
)
def post_document_message(
    request: Request,
    body: PostMessageRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """U9 — início/resposta de conversa pela Controladoria autorizada
    (`access` + escopo + documento da competência): não exige solicitação
    DRE prévia, não valida documento, não libera para Contabilidade e
    não altera pacote/fechamento. Autoria/data são do servidor; replay
    idempotente retorna a original (`deduplicated`), divergente 409."""
    user = authorized_user(request)
    try:
        message, created = _service().post_document_message(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            author_name=_author_name(user),
            body=body.body,
            idempotency_key=body.idempotency_key,
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "post_document_message")
    data = _message_view(message, mine=True)
    if not created:
        data["deduplicated"] = True
    return ok(
        data,
        message=(
            "Mensagem enviada."
            if created
            else "Mensagem já registrada para esta chave de idempotência."
        ),
        status_code=201 if created else 200,
        operation_id="post_document_message",
    )
