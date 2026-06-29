from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from delpi_auth.jwt_validator import validate_token

from app.composition.audit_5s_composer import build_audit_5s_repository
from app.shared.utils.person_name import format_person_name
from app.interface.socket.sio_server import sio
from app.utils.logger import log_error

_audit_presence: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
_observation_typing: dict[str, dict[str, dict[str, dict[str, str]]]] = defaultdict(lambda: defaultdict(dict))
_session_user: dict[str, dict[str, str]] = {}


def _room(audit_id: str) -> str:
    return f"audit:{audit_id}"


def _extract_token(auth: dict[str, Any] | None, environ: dict[str, Any]) -> str | None:
    if auth and isinstance(auth, dict):
        token = auth.get("token")
        if isinstance(token, str) and token.strip():
            return token.strip()

    query = environ.get("QUERY_STRING") or ""
    for part in query.split("&"):
        if part.startswith("token="):
            return part.split("=", 1)[1]
    return None


def _claims_display_name(claims: dict[str, Any]) -> str:
    for key in ("name", "preferred_username", "email", "sub"):
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return format_person_name(value.strip())
    return "Usuário"


async def _broadcast_presence(audit_id: str) -> None:
    members = _audit_presence.get(audit_id, {})
    # Um usuário pode ter várias abas (vários sid); presença exibe uma entrada por user_id.
    users_by_id: dict[str, dict[str, str]] = {}
    for entry in members.values():
        user_id = str(entry.get("user_id") or "").strip()
        if not user_id:
            continue
        users_by_id[user_id] = {
            "user_id": user_id,
            "display_name": str(entry.get("display_name") or "Usuário"),
        }
    users = list(users_by_id.values())
    await sio.emit(
        "audit5s.presence.updated",
        {"audit_id": audit_id, "users": users},
        room=_room(audit_id),
    )


def _list_typing_users(
    members: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    users: list[dict[str, str]] = []
    for sid, entry in members.items():
        user_id = str(entry.get("user_id") or "").strip()
        if not user_id:
            continue
        users.append(
            {
                "user_id": user_id,
                "display_name": str(entry.get("display_name") or "Usuário"),
                "client_id": str(entry.get("client_id") or sid).strip(),
            },
        )
    return users


async def _broadcast_observation_typing(audit_id: str, criterion_id: str) -> None:
    members = _observation_typing.get(audit_id, {}).get(criterion_id, {})
    await sio.emit(
        "audit5s.observation.typing.updated",
        {
            "audit_id": audit_id,
            "criterion_id": criterion_id,
            "users": _list_typing_users(members),
        },
        room=_room(audit_id),
    )


def _remove_sid_from_observation_typing(
    sid: str,
    audit_id: str | None = None,
) -> list[tuple[str, str]]:
    affected: list[tuple[str, str]] = []
    audit_ids = [audit_id] if audit_id else list(_observation_typing.keys())

    for aid in audit_ids:
        criteria = _observation_typing.get(aid)
        if not criteria:
            continue

        for criterion_id, members in list(criteria.items()):
            if sid not in members:
                continue
            members.pop(sid, None)
            affected.append((aid, criterion_id))
            if not members:
                criteria.pop(criterion_id, None)

        if not criteria:
            _observation_typing.pop(aid, None)

    return affected


def _register_auditor_sync(audit_id: str, user_id: str, display_name: str) -> None:
    repo = build_audit_5s_repository()
    repo.ensure_auditor(
        audit_id=audit_id,
        user_id=user_id,
        display_name=display_name,
    )


async def _clear_observation_typing_for_sid(
    sid: str,
    audit_id: str | None = None,
) -> None:
    affected = _remove_sid_from_observation_typing(sid, audit_id)
    for aid, criterion_id in affected:
        await _broadcast_observation_typing(aid, criterion_id)


def register_audit_5s_socket_handlers() -> None:
    @sio.event
    async def connect(sid, environ, auth):
        token = _extract_token(auth, environ or {})
        if not token:
            return False

        try:
            claims = validate_token(token)
        except Exception:
            return False

        user_id = str(claims.get("sub") or "").strip()
        if not user_id:
            return False

        display_name = _claims_display_name(claims)
        _session_user[sid] = {
            "user_id": user_id,
            "display_name": display_name,
        }
        await sio.save_session(
            sid,
            {"user_id": user_id, "display_name": display_name},
        )
        return True

    @sio.event
    async def disconnect(sid):
        _session_user.pop(sid, None)

        affected_audits: list[str] = []
        for audit_id, members in list(_audit_presence.items()):
            if sid in members:
                members.pop(sid, None)
                affected_audits.append(audit_id)
            if not members:
                _audit_presence.pop(audit_id, None)

        for audit_id in affected_audits:
            await _broadcast_presence(audit_id)

        await _clear_observation_typing_for_sid(sid)

    @sio.on("audit5s.join")
    async def audit5s_join(sid, data):
        if not isinstance(data, dict):
            return

        audit_id = str(data.get("auditId") or data.get("audit_id") or "").strip()
        if not audit_id:
            return

        session = await sio.get_session(sid)
        user_id = str(session.get("user_id") or _session_user.get(sid, {}).get("user_id") or "")
        display_name = str(
            session.get("display_name") or _session_user.get(sid, {}).get("display_name") or "Usuário",
        )
        if not user_id:
            return

        await sio.enter_room(sid, _room(audit_id))
        _audit_presence[audit_id][sid] = {
            "user_id": user_id,
            "display_name": display_name,
        }
        try:
            await asyncio.to_thread(
                _register_auditor_sync,
                audit_id,
                user_id,
                display_name,
            )
        except Exception as exc:
            log_error(f"Erro ao registrar auditor 5S no join: {exc}")
        await _broadcast_presence(audit_id)

    @sio.on("audit5s.leave")
    async def audit5s_leave(sid, data):
        if not isinstance(data, dict):
            return

        audit_id = str(data.get("auditId") or data.get("audit_id") or "").strip()
        if not audit_id:
            return

        await sio.leave_room(sid, _room(audit_id))
        members = _audit_presence.get(audit_id)
        if members and sid in members:
            members.pop(sid, None)
        if members is not None and not members:
            _audit_presence.pop(audit_id, None)
        await _broadcast_presence(audit_id)
        await _clear_observation_typing_for_sid(sid, audit_id)

    @sio.on("audit5s.observation.typing")
    async def audit5s_observation_typing(sid, data):
        if not isinstance(data, dict):
            return

        audit_id = str(data.get("auditId") or data.get("audit_id") or "").strip()
        criterion_id = str(data.get("criterionId") or data.get("criterion_id") or "").strip()
        if not audit_id or not criterion_id:
            return

        session = await sio.get_session(sid)
        user_id = str(session.get("user_id") or _session_user.get(sid, {}).get("user_id") or "")
        display_name = str(
            session.get("display_name") or _session_user.get(sid, {}).get("display_name") or "Usuário",
        )
        if not user_id:
            return

        client_id = str(data.get("clientId") or data.get("client_id") or sid).strip()
        _observation_typing[audit_id][criterion_id][sid] = {
            "user_id": user_id,
            "display_name": display_name,
            "client_id": client_id,
        }
        await _broadcast_observation_typing(audit_id, criterion_id)

    @sio.on("audit5s.observation.typing.stop")
    async def audit5s_observation_typing_stop(sid, data):
        if not isinstance(data, dict):
            return

        audit_id = str(data.get("auditId") or data.get("audit_id") or "").strip()
        criterion_id = str(data.get("criterionId") or data.get("criterion_id") or "").strip()
        if not audit_id or not criterion_id:
            return

        members = _observation_typing.get(audit_id, {}).get(criterion_id)
        if members and sid in members:
            members.pop(sid, None)
        if members is not None and not members:
            _observation_typing.get(audit_id, {}).pop(criterion_id, None)
        if audit_id in _observation_typing and not _observation_typing[audit_id]:
            _observation_typing.pop(audit_id, None)

        await _broadcast_observation_typing(audit_id, criterion_id)
