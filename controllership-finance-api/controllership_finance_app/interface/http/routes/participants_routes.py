"""UX-009 — perfil público de participantes (Plano 113 §23.3).

A Controladoria autorizada (`access` efetivo) resolve nome oficial e
foto de participantes que aparecem em conversas/eventos documentais.
Ownership do dado permanece no Core:

- nomes: `POST /me/directory/users/lookup` com o bearer do próprio
  caller (o diretório aplica a autorização do usuário; e-mails nunca
  são expostos — `mask_email` default);
- fotos: `GET /integrations/person-profiles/{id}/photo` via S2S
  (`CORE_API_INTEGRATIONS_SERVICE_TOKEN`), proxy read-through sem
  persistência local.

Não é uma nova fonte de identidade: perfil indisponível → campos
honestamente vazios/404 — a UI cai em fallback neutro (iniciais), nunca
em UUID nem em foto inventada.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.infrastructure.gateways.core_person_profile_gateway import (  # noqa: E501
    CorePersonProfileGateway,
)
from controllership_finance_app.interface.http.authz import authorized_user

router = APIRouter(prefix="/closing", tags=["Closing Participants"])

MAX_IDS = 50


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
    "/participants/lookup",
    operation_id="lookup_closing_participants",
)
def lookup_participants(request: Request, body: ParticipantLookupBody):
    """Resolve `display_name` + `has_photo` para até 50 participantes.

    Identificador fora do diretório (histórico/inativo) retorna
    `display_name = None` — identificação neutra fica com a UI."""
    authorized_user(request)
    ids = [
        str(uuid.UUID(str(raw)))
        for raw in body.ids
        if _is_uuid(str(raw))
    ][:MAX_IDS]
    gateway = _gateway()
    names = gateway.lookup_directory_names(
        ids, bearer_token=_bearer(request)
    )
    photos = gateway.lookup_has_photo(ids)
    items = [
        {
            "user_id": uid,
            "display_name": names.get(uid),
            "has_photo": bool(photos.get(uid)),
        }
        for uid in ids
    ]
    return ok(
        {"items": items},
        operation_id="lookup_closing_participants",
    )


@router.get(
    "/participants/{user_id}/avatar",
    operation_id="get_closing_participant_avatar",
)
def get_participant_avatar(request: Request, user_id: str):
    """Foto publicada do participante (proxy Core, read-through).

    404 = sem foto (fallback de iniciais na UI); 502 = Core indisponível
    ou payload inválido — nunca gera imagem artificial."""
    authorized_user(request)
    try:
        uid = str(uuid.UUID(str(user_id)))
    except (TypeError, ValueError):
        return fail(
            "user_id inválido.", 422, data={"code": "validation_error"}
        )
    gateway = _gateway()
    if not gateway.configured():
        return fail(
            "Perfil temporariamente indisponível.",
            503,
            data={"code": "person_profile_unavailable"},
        )
    photo = gateway.get_photo(uid)
    if photo is None:
        return fail("Foto não encontrada.", 404, data={"code": "not_found"})
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
