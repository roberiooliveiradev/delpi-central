from __future__ import annotations

import re

from tm_app.domain.entities.interaction_room import (
    LINK_ENTITY_HELPDESK_TICKET,
    LINK_ENTITY_PROCESS,
    LINK_ENTITY_TYPES,
    LINK_ROLES,
    ROOM_ACCESS_SCOPES,
)

MAX_MESSAGE_LENGTH = 4000
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def normalize_uuid(value: str | None, *, label: str) -> str:
    identifier = (value or "").strip()
    if not _UUID_RE.match(identifier):
        raise ValueError(f"{label} precisa ser um identificador válido.")
    return identifier


def normalize_processo_id(value: str | None) -> str:
    return normalize_uuid(value, label="O processo")


def normalize_inbox_filter(value: str | None) -> str:
    key = (value or "all").strip().lower()
    if key not in {"all", "process", "unread", "mentioned"}:
        raise ValueError("Filtro inválido.")
    return key


def normalize_reaction_code(value: str | None) -> str:
    code = (value or "").strip()
    if not code or len(code) > 32:
        raise ValueError("Reação inválida.")
    return code


def normalize_mentions(items: list[dict] | None) -> tuple[tuple[str, str], ...]:
    seen: dict[str, str] = {}
    for item in items or []:
        user_id = normalize_uuid(str(item.get("user_id") or ""), label="A pessoa mencionada")
        label = " ".join(str(item.get("label") or "").replace("@", " ").split())
        if not label:
            continue
        seen[user_id] = label[:80]
    return tuple(seen.items())


def normalize_message_content(value: str | None) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("A mensagem não pode ficar em branco.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"A mensagem pode ter no máximo {MAX_MESSAGE_LENGTH} caracteres.")
    return text


MAX_ROOM_TITLE_LENGTH = 120
_TICKET_KEY_RE = re.compile(r"^[0-9]{1,20}$")


def normalize_room_title(value: str | None) -> str:
    title = " ".join((value or "").split())
    if not title:
        raise ValueError("A sala precisa de um título.")
    if len(title) > MAX_ROOM_TITLE_LENGTH:
        raise ValueError(f"O título pode ter no máximo {MAX_ROOM_TITLE_LENGTH} caracteres.")
    return title


def normalize_access_scope(value: str | None) -> str:
    scope = (value or "").strip().lower()
    if scope not in ROOM_ACCESS_SCOPES:
        raise ValueError("Escopo de acesso inválido.")
    return scope


def normalize_link_role(value: str | None) -> str:
    role = (value or "").strip().lower()
    if role not in LINK_ROLES:
        raise ValueError("Papel de vínculo inválido.")
    return role


def normalize_link_entity(value: str | None) -> str:
    entity_type = (value or "").strip().lower()
    if entity_type not in LINK_ENTITY_TYPES:
        raise ValueError("Tipo de objeto vinculado inválido.")
    return entity_type


def normalize_entity_key(entity_type: str, value: str | None) -> str:
    key = (value or "").strip()
    if entity_type == LINK_ENTITY_PROCESS:
        return normalize_uuid(key, label="O processo vinculado")
    if entity_type == LINK_ENTITY_HELPDESK_TICKET:
        if not _TICKET_KEY_RE.match(key):
            raise ValueError("O chamado vinculado precisa ser um identificador numérico válido.")
        return key
    raise ValueError("Tipo de objeto vinculado inválido.")
