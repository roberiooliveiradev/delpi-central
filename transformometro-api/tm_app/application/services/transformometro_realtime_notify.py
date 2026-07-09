from __future__ import annotations

from typing import Any

from tm_app.application.services.transformometro_realtime_hub import (
    transformometro_realtime_hub,
)

SECTION_KEY_BY_ACTION: dict[str, str] = {
    "diagram.macro.updated": "diagrama_macro",
    "diagram.macro.imported_bpmn": "diagrama_macro",
    "diagram.escopo.updated": "diagrama_escopo",
    "diagram.overlay.updated": "diagrama_revisao",
    "decomposition.updated": "decomposicao",
    "decomposition.scope.updated": "decomposicao_escopo",
    "decomposition.context.updated": "decomposicao_contexto",
    "decomposition.overlay.updated": "decomposicao_overlay",
    "processo.arquivo.created": "arquivos",
    "processo.arquivo.updated": "arquivos",
    "processo.arquivo.deleted": "arquivos",
    "update": "processo",
    "create": "processo",
    "upsert": "medicao",
    "activate": "vigencia",
}


def room_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"


def infer_section_key(entity_type: str, action: str) -> str | None:
    if action in SECTION_KEY_BY_ACTION:
        return SECTION_KEY_BY_ACTION[action]
    if entity_type == "processo":
        return "processo"
    if entity_type == "processo_instancia":
        return "instancia"
    if entity_type == "revisao":
        return "vigencia"
    if entity_type == "medicao":
        return "medicao"
    if entity_type == "investimento":
        return "investimentos"
    if entity_type == "vinculo":
        return "recursos"
    if entity_type == "filial":
        return "filial"
    if entity_type == "setor":
        return "setor"
    if entity_type == "recurso":
        return "recurso"
    if entity_type == "recurso_custo":
        return "custos"
    return None


def _related_rooms(entity_type: str, entity_id: str, payload: dict[str, Any]) -> list[str]:
    rooms = [room_key(entity_type, entity_id)]
    revisao_id = payload.get("revisao_id")
    if revisao_id and entity_type in {"medicao", "investimento", "vinculo"}:
        rooms.append(room_key("revisao", str(revisao_id)))
    processo_id = payload.get("processo_id")
    if processo_id and entity_type == "processo_instancia":
        rooms.append(room_key("processo", str(processo_id)))
    return list(dict.fromkeys(rooms))


def notify_presence_updated(
    *,
    entity_type: str,
    entity_id: str,
    presence: dict[str, Any],
) -> None:
    payload = {
        "type": "presence.updated",
        "entityType": entity_type,
        "entityId": entity_id,
        "data": presence,
    }
    transformometro_realtime_hub.schedule_broadcast(
        room_key(entity_type, entity_id),
        payload,
    )


def notify_entity_updated(
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_user_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    body = payload or {}
    event = {
        "type": "entity.updated",
        "entityType": entity_type,
        "entityId": entity_id,
        "action": action,
        "sectionKey": infer_section_key(entity_type, action),
        "actorUserId": actor_user_id,
        "payload": body,
    }
    for room in _related_rooms(entity_type, entity_id, body):
        transformometro_realtime_hub.schedule_broadcast(room, event)


def notify_from_audit(
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_user_id: str | None,
    payload: dict[str, Any],
) -> None:
    notify_entity_updated(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_user_id,
        payload=payload,
    )
