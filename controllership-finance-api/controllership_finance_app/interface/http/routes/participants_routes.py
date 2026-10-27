"""RW01 — perfil de participantes vinculados ao documento (Plano 113 §23.6).

Correção de isolamento da UX-009: identidade/foto só são resolvidas
depois de `capability` (`access` efetivo) + `resource_scope`
(`_document_in_scope`: competência do path + filial-contexto, cross =
404) + `business_rule` (vínculo canônico do participante: autor de
mensagem U9, ator de evento U8 ou uploader do documento). Participante
fora do documento recebe o mesmo 404 do recurso inexistente —
existência de pessoa, documento ou competência nunca vaza, e não há
consulta livre ao diretório pela superfície documental.

Ownership do dado permanece no Core (`core-api`):

- nomes: `POST /me/directory/users/lookup` com o bearer do próprio
  caller (a autorização de leitura do diretório continua sendo a do
  usuário; e-mails nunca são repassados — `mask_email` default);
- fotos: `GET /integrations/person-profiles/{id}/photo` via S2S
  (`CORE_API_INTEGRATIONS_SERVICE_TOKEN`), proxy read-through sem
  persistência local.

Não é uma nova fonte de identidade: perfil indisponível → campos
honestamente vazios/404 — a UI cai em fallback neutro (iniciais), nunca
em UUID nem em foto inventada.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from controllership_finance_app.application.services.closing_document_service import (  # noqa: E501
    ClosingDocumentService,
)
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.gateways.core_person_profile_gateway import (  # noqa: E501
    CorePersonProfileGateway,
)
from controllership_finance_app.interface.http.authz import authorized_user

router = APIRouter(
    prefix="/closing/competences", tags=["Closing Participants"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
MAX_IDS = 50


def _service() -> ClosingDocumentService:
    return ClosingDocumentService()


def _gateway() -> CorePersonProfileGateway:
    return CorePersonProfileGateway()


def _bearer(request: Request) -> str:
    return (request.headers.get("Authorization") or "").strip()


def _is_uuid(raw: str) -> bool:
    try:
        uuid.UUID(str(raw).strip())
    except (TypeError, ValueError):
        return False
    return True


class ParticipantLookupBody(BaseModel):
    ids: list[str] = Field(default_factory=list, max_length=MAX_IDS)


@router.post(
    "/{period}/documents/{document_id}/participants/lookup",
    operation_id="lookup_document_participants",
)
def lookup_participants(
    request: Request,
    body: ParticipantLookupBody,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """Resolve `display_name` + `has_photo` somente para participantes
    vinculados ao documento autorizado (autor U9, ator U8 ou uploader).

    Ids sem vínculo são omitidos da resposta — a ausência não confirma
    nem nega a existência da pessoa (fail-closed, sem enumeração).
    Identificador histórico/inativo retorna `display_name = None`."""
    authorized_user(request)
    try:
        bound = _service().document_participant_ids(
            period=period,
            document_id=str(document_id),
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return fail(
            exc.message,
            exc.status,
            data={"error": {"code": exc.code}},
            operation_id="lookup_document_participants",
        )
    ids = [
        str(uuid.UUID(str(raw)))
        for raw in body.ids
        if _is_uuid(str(raw))
    ]
    allowed = [uid for uid in ids if uid in bound][:MAX_IDS]
    if not allowed:
        return ok(
            {"items": []},
            operation_id="lookup_document_participants",
        )
    gateway = _gateway()
    names = gateway.lookup_directory_names(
        allowed, bearer_token=_bearer(request)
    )
    photos = gateway.lookup_has_photo(allowed)
    items = [
        {
            "user_id": uid,
            "display_name": names.get(uid),
            "has_photo": bool(photos.get(uid)),
        }
        for uid in allowed
    ]
    return ok(
        {"items": items},
        operation_id="lookup_document_participants",
    )


@router.get(
    "/{period}/documents/{document_id}/participants/{user_id}/avatar",
    operation_id="get_document_participant_avatar",
)
def get_participant_avatar(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    user_id: str = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """Foto publicada do participante vinculado ao documento (proxy
    Core, read-through).

    Participante sem vínculo canônico → mesmo 404 de recurso
    inexistente (existência nunca vaza). 404 também = sem foto
    publicada; 503 = Core indisponível — nunca gera imagem artificial."""
    authorized_user(request)
    try:
        uid = str(uuid.UUID(str(user_id)))
    except (TypeError, ValueError):
        return fail(
            "user_id inválido.",
            422,
            data={"error": {"code": "validation_error"}},
            operation_id="get_document_participant_avatar",
        )
    try:
        bound = _service().document_participant_ids(
            period=period,
            document_id=str(document_id),
            branch_scope=branch_scope,
        )
    except ChecklistDomainError as exc:
        return fail(
            exc.message,
            exc.status,
            data={"error": {"code": exc.code}},
            operation_id="get_document_participant_avatar",
        )
    if uid not in bound:
        return fail(
            "Foto não encontrada.",
            404,
            data={"error": {"code": "not_found"}},
            operation_id="get_document_participant_avatar",
        )
    gateway = _gateway()
    if not gateway.configured():
        return fail(
            "Perfil temporariamente indisponível.",
            503,
            data={"error": {"code": "person_profile_unavailable"}},
            operation_id="get_document_participant_avatar",
        )
    photo = gateway.get_photo(uid)
    if photo is None:
        return fail(
            "Foto não encontrada.",
            404,
            data={"error": {"code": "not_found"}},
            operation_id="get_document_participant_avatar",
        )
    content, content_type, file_name = photo
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Cache-Control": "private, max-age=300",
            "X-Content-Type-Options": "nosniff",
        },
    )
