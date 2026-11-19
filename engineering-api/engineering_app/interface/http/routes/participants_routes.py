"""BFF de participantes — proxy governado do avatar canônico do Portal
(Core ``/integrations/person-profiles`` via S2S). Ownership da foto
permanece na Core; aqui só autorização do módulo + repasse de bytes.
Mesmo contrato do requests-api (``/participants``).

Sem ``from __future__ import annotations``: endpoints decorados por
``require_any_permission`` resolvem ForwardRefs no globalns do wrapper
(delpi_auth), não do módulo — anotações precisam ser objetos reais."""

from fastapi import APIRouter, Body
from fastapi.responses import Response
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission

from engineering_app.core.responses import fail, ok
from engineering_app.domain.product_registration.models import ENG_ACCESS
from engineering_app.infrastructure.gateways.core_person_profile_adapter import (
    CorePersonProfileAdapter,
)

router = APIRouter()

_PARTICIPANT_PERMS = [ENG_ACCESS]


class ParticipantLookupBody(BaseModel):
    ids: list[str] = Field(default_factory=list, max_length=50)


@router.post("/v1/participants/lookup", operation_id="participants_lookup")
@require_any_permission(_PARTICIPANT_PERMS)
def participants_lookup(body: ParticipantLookupBody = Body(...)):
    """Batch has_photo da Core person-profile (S2S). Sem PII privada."""
    adapter = CorePersonProfileAdapter()
    ids = [uid for uid in (str(i).strip() for i in body.ids) if uid]
    has_map = adapter.lookup_has_photo(ids)
    items = [
        {"user_id": uid, "has_photo": bool(has_map.get(uid))} for uid in ids
    ]
    return ok({"items": items})


@router.get(
    "/v1/participants/{user_id}/avatar",
    operation_id="participants_avatar",
)
@require_any_permission(_PARTICIPANT_PERMS)
def participants_avatar(user_id: str):
    """Proxy da foto canônica do Portal (Core). 404 → iniciais no MFE."""
    uid = (user_id or "").strip()
    if not uid:
        return fail("user_id inválido.", 422, data={"code": "validation_error"})
    photo = CorePersonProfileAdapter().get_photo(uid)
    if photo is None:
        return fail("Foto não encontrada.", 404, data={"code": "not_found"})
    content, content_type, file_name = photo
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )
