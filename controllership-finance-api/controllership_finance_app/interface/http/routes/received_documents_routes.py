"""DRE-019 — superfície documental do destinatário externo.

`GET/POST /closing/received-documents*` — projeção restrita do mesmo
domínio (doc 91 Opção B, Plano 113 §29, doc 112 §54):

- capability `controllership-finance.closing-documents.read` efetiva —
  NÃO implica `access`/`manage` e não alcança nenhuma rota interna;
- vínculo RECIPIENT + pacote SUBMITTED + membership no conjunto
  liberado são reavaliados por request no serviço — a permission
  sozinha não revela recurso algum (fail-closed);
- todo recurso fora do conjunto liberado é 404 — existência de
  competência, pacote, documento ou versão nunca vaza por status;
- download reusa o storage autenticado + auditoria
  `DOCUMENT_DOWNLOADED` do contrato interno (decisão de autorização,
  nunca entrega concluída) — sem URL pública, sem storage_key;
- mensagens do destinatário são sempre `SHARED`; INTERNAL nunca sai
  nesta superfície;
- solicitações de ajuste seguem OPEN → ANSWERED → CONFIRMED: a
  resposta da Controladoria não encerra — conclusão só do requerente.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from controllership_finance_app.application.services.received_documents_service import (
    ReceivedDocumentsService,
)
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.interface.http.authz import (
    actor_subject,
    authorized_documents_reader,
)

router = APIRouter(
    prefix="/closing/received-documents",
    tags=["Received Documents"],
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


def _service() -> ReceivedDocumentsService:
    return ReceivedDocumentsService()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _author_name(user) -> str | None:
    """Nome de exibição do ator autenticado (claim `name` do middleware)
    — ausência fica NULL e a UI resolve identificação neutra, nunca o
    UUID como nome."""
    name = (getattr(user, "name", None) or "").strip()
    return name if name and "@" not in name else None


@router.get(
    "",
    operation_id="list_received_deliveries",
)
def list_received_deliveries(request: Request):
    """«Fechamentos recebidos» — entregas correntes com vínculo
    RECIPIENT ativo do ator (capability + vínculo + SUBMITTED)."""
    user = authorized_documents_reader(request)
    try:
        deliveries = _service().list_deliveries(
            actor=actor_subject(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_received_deliveries")
    return ok(
        {"deliveries": deliveries},
        operation_id="list_received_deliveries",
    )


@router.get(
    "/{period}",
    operation_id="get_received_delivery",
)
def get_received_delivery(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    """Entrega da competência: envios vigentes + documentos liberados
    + solicitações do próprio ator — projeção sem dados internos."""
    user = authorized_documents_reader(request)
    try:
        delivery = _service().get_delivery(
            period=period, actor=actor_subject(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_received_delivery")
    return ok(delivery, operation_id="get_received_delivery")


@router.get(
    "/{period}/documents/{document_id}",
    operation_id="get_received_document",
)
def get_received_document(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
):
    """Detalhe do documento liberado + versões autorizadas (todas as
    versões pinadas em SUBMITTED dos pacotes vinculados)."""
    user = authorized_documents_reader(request)
    try:
        detail = _service().get_document(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_received_document")
    return ok(detail, operation_id="get_received_document")


@router.get(
    "/{period}/documents/{document_id}/versions/{version_no}/content",
    operation_id="download_received_document_version",
)
def download_received_document_version(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    version_no: int = Path(ge=1),
):
    """Stream autenticado — somente versão pinada em SUBMITTED dos
    pacotes vinculados; `DOCUMENT_DOWNLOADED` registra AUTHORIZED/
    DENIED/FAILED (decisão de autorização, nunca entrega)."""
    user = authorized_documents_reader(request)
    try:
        path, meta = _service().resolve_download(
            period=period,
            document_id=str(document_id),
            version_no=version_no,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "download_received_document_version")
    return FileResponse(
        path,
        media_type=meta["mime_type"],
        filename=meta["original_name"],
    )


def _message_view(row: dict, *, mine: bool | None = None) -> dict:
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


class PostReceivedMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=128)


@router.get(
    "/{period}/documents/{document_id}/messages",
    operation_id="list_received_document_messages",
)
def list_received_document_messages(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Conversa compartilhada — somente `SHARED`; INTERNAL nunca sai."""
    user = authorized_documents_reader(request)
    try:
        result = _service().list_messages(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            limit=limit,
            offset=offset,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_received_document_messages")
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
        operation_id="list_received_document_messages",
    )


@router.post(
    "/{period}/documents/{document_id}/messages",
    operation_id="post_received_document_message",
    status_code=201,
)
def post_received_document_message(
    request: Request,
    body: PostReceivedMessageRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
):
    """Mensagem do destinatário — sempre `SHARED`, autoria/data do
    servidor, carimbo da versão liberada corrente; replay idempotente
    retorna a original (`deduplicated`), divergente 409."""
    user = authorized_documents_reader(request)
    try:
        message, created = _service().post_message(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            author_name=_author_name(user),
            body=body.body,
            idempotency_key=body.idempotency_key,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "post_received_document_message")
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
        operation_id="post_received_document_message",
    )


class PostAdjustmentRequestBody(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=128)


@router.get(
    "/{period}/documents/{document_id}/adjustment-requests",
    operation_id="list_received_adjustment_requests",
)
def list_received_adjustment_requests(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
):
    """Solicitações do próprio ator no documento liberado — pedidos
    de outros destinatários nunca são listados."""
    user = authorized_documents_reader(request)
    try:
        requests_list = _service().list_requests(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_received_adjustment_requests")
    return ok(
        {"requests": requests_list},
        operation_id="list_received_adjustment_requests",
    )


@router.post(
    "/{period}/documents/{document_id}/adjustment-requests",
    operation_id="create_received_adjustment_request",
    status_code=201,
)
def create_received_adjustment_request(
    request: Request,
    body: PostAdjustmentRequestBody,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
):
    """Solicitação de esclarecimento/revisão — autor, data, motivo e
    versão contextual do servidor; replay idempotente deduplica."""
    user = authorized_documents_reader(request)
    try:
        created_request, created = _service().create_request(
            period=period,
            document_id=str(document_id),
            actor=actor_subject(user),
            author_name=_author_name(user),
            body=body.body,
            idempotency_key=body.idempotency_key,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_received_adjustment_request")
    data = dict(created_request)
    if not created:
        data["deduplicated"] = True
    return ok(
        data,
        message=(
            "Solicitação registrada."
            if created
            else "Solicitação já registrada para esta chave de "
            "idempotência."
        ),
        status_code=201 if created else 200,
        operation_id="create_received_adjustment_request",
    )


@router.post(
    "/{period}/documents/{document_id}/adjustment-requests/"
    "{request_id}/confirm",
    operation_id="confirm_received_adjustment_request",
)
def confirm_received_adjustment_request(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    request_id: uuid.UUID = Path(),
):
    """Conclusão pelo requerente — ANSWERED → CONFIRMED, somente o
    autor; a resposta da Controladoria nunca encerra sozinha."""
    user = authorized_documents_reader(request)
    try:
        confirmed = _service().confirm_request(
            period=period,
            document_id=str(document_id),
            request_id=str(request_id),
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "confirm_received_adjustment_request")
    return ok(
        confirmed,
        message="Solicitação concluída.",
        operation_id="confirm_received_adjustment_request",
    )
