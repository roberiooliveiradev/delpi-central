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
    # Alinhado ao section_key do MFE (RevisaoCadastroPanel / collaborationSections).
    "decomposition.overlay.updated": "decomposicao_revisao",
    "processo.arquivo.created": "arquivos",
    "processo.arquivo.updated": "arquivos",
    "processo.arquivo.deleted": "arquivos",
    "revisao.evidencia.created": "evidencias",
    "revisao.evidencia.updated": "evidencias",
    "revisao.evidencia.deleted": "evidencias",
    "matrix.updated": "matriz",
    "upsert": "medicao",
    "activate": "vigencia",
    "reajuste": "custos",
    "import_replace": "catalog",
    "import_merge": "catalog",
    "recalcular": "dashboard",
}

# entity_type → id da sala catalog:<id> (listagens / dashboard)
CATALOG_ROOM_BY_ENTITY: dict[str, str] = {
    "processo": "processo",
    "processo_instancia": "processo",
    "revisao": "processo",
    "medicao": "dashboard",
    "investimento": "dashboard",
    "vinculo": "dashboard",
    "filial": "filial",
    "setor": "setor",
    "recurso": "recurso",
    "recurso_custo": "recurso",
    "catalog": "dashboard",
    "json_backup": "dashboard",
}

CRUD_ACTIONS = frozenset({"create", "update", "delete", "duplicate"})


def room_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"


def catalog_room(catalog_id: str) -> str:
    return room_key("catalog", catalog_id)


def infer_section_key(entity_type: str, action: str) -> str | None:
    if action in SECTION_KEY_BY_ACTION:
        return SECTION_KEY_BY_ACTION[action]
    if action in CRUD_ACTIONS:
        if entity_type == "processo":
            return "processo"
        if entity_type == "processo_instancia":
            return "instancia"
        if entity_type == "revisao":
            return "vigencia"
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
        if entity_type == "medicao":
            return "medicao"
        if entity_type == "catalog":
            return "catalog"
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
    if entity_type == "catalog":
        return "catalog"
    return None


def _lookup_revisao_scope(revisao_id: str) -> tuple[str | None, str | None]:
    """processo_id, instancia_id a partir da revisão (best-effort)."""
    try:
        from tm_app.infrastructure.persistence.repositories.revisao_repository import (
            RevisaoRepository,
        )

        row = RevisaoRepository().get(str(revisao_id))
    except Exception:
        return None, None
    if not row:
        return None, None
    processo_id = row.get("processo_id")
    instancia_id = row.get("instancia_id")
    return (
        str(processo_id) if processo_id else None,
        str(instancia_id) if instancia_id else None,
    )


def _lookup_instancia_processo_id(instancia_id: str) -> str | None:
    try:
        from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
            ProcessoInstanciaRepository,
        )

        row = ProcessoInstanciaRepository().get(str(instancia_id))
    except Exception:
        return None
    if not row:
        return None
    processo_id = row.get("processo_id")
    return str(processo_id) if processo_id else None


def _lookup_recurso_vinculo_scopes(
    recurso_id: str,
) -> list[tuple[str, str | None, str | None]]:
    """(revisao_id, processo_id, instancia_id) das revisões que usam o recurso."""
    try:
        from tm_app.infrastructure.persistence.repositories.recurso_repository import (
            RecursoRepository,
        )

        rows = RecursoRepository().list_by_recurso(str(recurso_id))
    except Exception:
        return []
    scopes: list[tuple[str, str | None, str | None]] = []
    seen: set[str] = set()
    for row in rows or []:
        revisao_id = row.get("revisao_id")
        if not revisao_id:
            continue
        rid = str(revisao_id)
        if rid in seen:
            continue
        seen.add(rid)
        processo_id = row.get("processo_id")
        instancia_id = row.get("instancia_id")
        if not instancia_id:
            _, instancia_id = _lookup_revisao_scope(rid)
        scopes.append(
            (
                rid,
                str(processo_id) if processo_id else None,
                str(instancia_id) if instancia_id else None,
            )
        )
    return scopes


def enrich_realtime_scope_payload(
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Completa processo_id/instancia_id quando o audit omite (overlay diagrama/WBS,
    update vigência, escopo da instância). Permite fan-out sem depender de cada rota.
    """
    body = dict(payload or {})

    if entity_type == "revisao":
        if not body.get("processo_id") or not body.get("instancia_id"):
            processo_id, instancia_id = _lookup_revisao_scope(entity_id)
            if processo_id and not body.get("processo_id"):
                body["processo_id"] = processo_id
            if instancia_id and not body.get("instancia_id"):
                body["instancia_id"] = instancia_id
        return body

    if entity_type == "processo_instancia" and not body.get("processo_id"):
        processo_id = _lookup_instancia_processo_id(entity_id)
        if processo_id:
            body["processo_id"] = processo_id
        return body

    if entity_type in {"medicao", "investimento", "vinculo"}:
        revisao_id = body.get("revisao_id")
        if revisao_id and (not body.get("processo_id") or not body.get("instancia_id")):
            processo_id, instancia_id = _lookup_revisao_scope(str(revisao_id))
            if processo_id and not body.get("processo_id"):
                body["processo_id"] = processo_id
            if instancia_id and not body.get("instancia_id"):
                body["instancia_id"] = instancia_id

    return body


def _related_rooms(entity_type: str, entity_id: str, payload: dict[str, Any]) -> list[str]:
    rooms: list[str] = []
    if entity_type != "catalog":
        rooms.append(room_key(entity_type, entity_id))

    revisao_id = payload.get("revisao_id")
    if revisao_id and entity_type in {"medicao", "investimento", "vinculo"}:
        rooms.append(room_key("revisao", str(revisao_id)))
        # Matriz/comparativo da melhoria e árvore do processo precisam invalidar.
        instancia_id_op = payload.get("instancia_id")
        processo_id_op = payload.get("processo_id")
        if instancia_id_op:
            rooms.append(room_key("processo_instancia", str(instancia_id_op)))
        if processo_id_op:
            rooms.append(room_key("processo", str(processo_id_op)))

    processo_id = payload.get("processo_id")
    if processo_id and entity_type in {"processo_instancia", "revisao"}:
        rooms.append(room_key("processo", str(processo_id)))

    instancia_id = payload.get("instancia_id")
    if instancia_id and entity_type == "revisao":
        rooms.append(room_key("processo_instancia", str(instancia_id)))

    recurso_id = payload.get("recurso_compartilhado_id") or payload.get("recurso_id")
    if recurso_id and entity_type == "recurso_custo":
        rooms.append(room_key("recurso", str(recurso_id)))
        for revisao_id, processo_id_v, instancia_id_v in _lookup_recurso_vinculo_scopes(
            str(recurso_id)
        ):
            rooms.append(room_key("revisao", revisao_id))
            if instancia_id_v:
                rooms.append(room_key("processo_instancia", instancia_id_v))
            if processo_id_v:
                rooms.append(room_key("processo", processo_id_v))

    catalog_id = CATALOG_ROOM_BY_ENTITY.get(entity_type)
    if catalog_id:
        rooms.append(catalog_room(catalog_id))
    # Mutações operacionais também invalidam o dashboard ao vivo
    if entity_type in {
        "processo",
        "processo_instancia",
        "revisao",
        "medicao",
        "investimento",
        "vinculo",
        "recurso",
        "recurso_custo",
        "filial",
        "setor",
    }:
        rooms.append(catalog_room("dashboard"))

    # Import JSON / backup: refresh de todas as listagens
    if entity_type == "json_backup" or (
        entity_type == "catalog" and str(entity_id) == "all"
    ):
        for cid in ("processo", "filial", "setor", "recurso", "dashboard"):
            rooms.append(catalog_room(cid))

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
    actor_client_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    body = enrich_realtime_scope_payload(entity_type, entity_id, payload)
    event = {
        "type": "entity.updated",
        "entityType": entity_type,
        "entityId": entity_id,
        "action": action,
        "sectionKey": infer_section_key(entity_type, action),
        "actorUserId": actor_user_id,
        "actorClientId": actor_client_id,
        "payload": body,
    }
    for room in _related_rooms(entity_type, entity_id, body):
        transformometro_realtime_hub.schedule_broadcast(room, event)


def notify_catalog_updated(
    *,
    catalog_id: str,
    action: str,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    notify_entity_updated(
        entity_type="catalog",
        entity_id=catalog_id,
        action=action,
        actor_user_id=actor_user_id,
        actor_client_id=actor_client_id,
        payload=payload,
    )


def notify_from_audit(
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_user_id: str | None,
    payload: dict[str, Any],
    actor_client_id: str | None = None,
) -> None:
    notify_entity_updated(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_user_id,
        actor_client_id=actor_client_id,
        payload=payload,
    )
