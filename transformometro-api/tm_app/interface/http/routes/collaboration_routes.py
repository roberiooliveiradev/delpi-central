from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tm_app.application.services.collaboration_presence_service import (
    CollaborationPresenceService,
)
from tm_app.application.services.transformometro_realtime_collaboration import (
    transformometro_realtime_collaboration,
)
from tm_app.application.services.transformometro_realtime_notify import (
    notify_presence_updated,
)
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.responses import fail, ok

router = APIRouter(prefix="/transformometro/colaboracao", tags=["Transformômetro — colaboração"])

_service = CollaborationPresenceService()


def _broadcast_presence(entity_type: str, entity_id: str) -> None:
    try:
        payload = _service.list_presence(entity_type=entity_type, entity_id=entity_id)
        notify_presence_updated(
            entity_type=entity_type,
            entity_id=entity_id,
            presence=payload,
        )
    except ValueError:
        return


class HeartbeatBody(BaseModel):
    entity_type: str
    entity_id: str
    section_key: str = ""
    mode: str = "viewing"


class LockBody(BaseModel):
    entity_type: str
    entity_id: str
    section_key: str = ""


@router.get("/presenca")
def get_presenca(entity_type: str, entity_id: str):
    try:
        payload = _service.list_presence(entity_type=entity_type, entity_id=entity_id)
    except ValueError as exc:
        return fail(str(exc), 400)
    return ok(payload, "Presença colaborativa da entidade.")


@router.post("/presenca")
def post_presenca(body: HeartbeatBody, request: Request):
    user_id, user_email, user_name = actor_from_request(request)
    if not user_id:
        return fail("Usuário não autenticado.", 401)
    try:
        row = _service.heartbeat(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            section_key=body.section_key,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            mode=body.mode,
        )
    except ValueError as exc:
        return fail(str(exc), 400)
    _broadcast_presence(body.entity_type, body.entity_id)
    return ok(row, "Presença atualizada.")


@router.post("/travar")
def post_travar(body: LockBody, request: Request):
    user_id, user_email, user_name = actor_from_request(request)
    if not user_id:
        return fail("Usuário não autenticado.", 401)
    try:
        result = _service.acquire_lock(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            section_key=body.section_key,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
        )
    except ValueError as exc:
        return fail(str(exc), 400)
    if not result.get("acquired"):
        return fail(
            f"Seção em edição por {result['holder']['user_name'] or 'outro usuário'}.",
            409,
            data=result,
        )
    _broadcast_presence(body.entity_type, body.entity_id)
    return ok(result, "Trava de edição adquirida.")


@router.post("/liberar")
def post_liberar(body: LockBody, request: Request):
    user_id, _, _ = actor_from_request(request)
    if not user_id:
        return fail("Usuário não autenticado.", 401)
    try:
        _service.release_lock(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            section_key=body.section_key,
            user_id=user_id,
        )
    except ValueError as exc:
        return fail(str(exc), 400)
    _broadcast_presence(body.entity_type, body.entity_id)
    return ok({"released": True}, "Trava liberada.")


@router.delete("/presenca")
def delete_presenca(entity_type: str, entity_id: str, request: Request):
    user_id, _, _ = actor_from_request(request)
    if not user_id:
        return fail("Usuário não autenticado.", 401)
    try:
        cleared = transformometro_realtime_collaboration.clear_user_presence_http(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
        )
    except ValueError as exc:
        return fail(str(exc), 400)
    if not cleared:
        return ok({"cleared": False, "still_connected": True}, "Conexão em tempo real ainda ativa.")
    return ok({"cleared": True}, "Presença removida.")
