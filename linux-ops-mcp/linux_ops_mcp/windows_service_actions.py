"""ATLAS Windows service control tools — prepare/confirm only; never confirmed=true.

Deploy PREPARE/ACT modules are intentionally not imported here.
"""
from __future__ import annotations

import asyncio
from typing import Any, Literal

from .multiserver import ambiguous_hostname_payload, resolve_server_or_candidates
from .reader import ItPortalReader, ReadError, Settings
from .windows_control_client import WindowsControlClient

ControlAction = Literal["start", "stop", "restart"]
_ACTIONS = frozenset({"start", "stop", "restart"})
_TERMINAL = frozenset({"succeeded", "failed", "timeout"})
_POLL_ATTEMPTS = 12
_POLL_INTERVAL_SECONDS = 1.0


def _safe_error(code: str) -> dict[str, Any]:
    return {"ok": False, "error": code}


async def prepare_windows_service_action(
    *,
    authorization: str,
    action: ControlAction,
    server_id: str | None = None,
    hostname: str | None = None,
    service_name: str,
    include_archived: bool = False,
    settings: Settings | None = None,
    transport=None,
) -> dict[str, Any]:
    if action not in _ACTIONS:
        return _safe_error("invalid_control_action")
    if not isinstance(service_name, str) or not service_name.strip():
        return _safe_error("invalid_service_name")
    reader = ItPortalReader(settings or Settings.from_environment(require_legacy_server_id=False), transport=transport)
    client = WindowsControlClient(reader.settings, transport=transport)
    try:
        resolved = await resolve_server_or_candidates(
            reader,
            authorization,
            server_id=server_id,
            hostname=hostname,
            include_archived=include_archived,
        )
        if resolved.get("__ambiguous__"):
            return ambiguous_hostname_payload(resolved["__ambiguous__"])
        server = resolved
        prepared = await client.prepare_action(
            authorization,
            server["id"],
            service_name.strip(),
            action,
        )
        return {
            "ok": True,
            "status": "confirmation_required",
            "confirmation_id": prepared["confirmation_id"],
            "server_id": server["id"],
            "server_name": server.get("name"),
            "hostname": server.get("hostname"),
            "service_key": prepared["service_key"],
            "service_name": prepared["service_name"],
            "action": prepared["action"],
            "state_before": prepared["state_before"],
            "expires_at": prepared["expires_at"],
            "message": (
                f"O serviço {prepared['service_name']} está "
                f"{_state_label(prepared['state_before'])} no servidor "
                f"{server.get('name') or server.get('hostname')}. "
                f"Você solicitou {_action_label(action)}. "
                "Esta operação poderá provocar interrupção temporária. "
                "Confirme com confirm_windows_service_action e user_confirmed=true."
            ),
        }
    except ReadError as exc:
        return _safe_error(exc.code)
    except Exception:
        return _safe_error("control_unavailable")


async def confirm_windows_service_action(
    *,
    authorization: str,
    confirmation_id: str,
    user_confirmed: bool,
    server_id: str | None = None,
    hostname: str | None = None,
    service_name: str,
    action: ControlAction,
    include_archived: bool = False,
    settings: Settings | None = None,
    transport=None,
    poll: bool = True,
) -> dict[str, Any]:
    if not user_confirmed:
        return _safe_error("user_confirmation_required")
    if action not in _ACTIONS:
        return _safe_error("invalid_control_action")
    if not isinstance(service_name, str) or not service_name.strip():
        return _safe_error("invalid_service_name")
    reader = ItPortalReader(settings or Settings.from_environment(require_legacy_server_id=False), transport=transport)
    client = WindowsControlClient(reader.settings, transport=transport)
    try:
        resolved = await resolve_server_or_candidates(
            reader,
            authorization,
            server_id=server_id,
            hostname=hostname,
            include_archived=include_archived,
        )
        if resolved.get("__ambiguous__"):
            return ambiguous_hostname_payload(resolved["__ambiguous__"])
        server = resolved
        queued = await client.confirm_action(
            authorization,
            server["id"],
            service_name.strip(),
            action,
            confirmation_id,
        )
        final = queued
        if poll:
            final = await _poll_until_terminal(
                client, authorization, server["id"], queued["id"],
            )
        observed = await _observe_service(
            reader, authorization, server["id"], queued.get("service_key") or service_name,
        )
        status = final.get("status") or "unconfirmed"
        proven = status == "succeeded" and final.get("state_after") in {"running", "stopped"}
        return {
            "ok": True,
            "status": status if status in _TERMINAL else "unconfirmed",
            "proven": proven,
            "action_id": final.get("id") or queued["id"],
            "server_id": server["id"],
            "server_name": server.get("name"),
            "hostname": server.get("hostname"),
            "service_key": final.get("service_key") or queued.get("service_key"),
            "service_name": final.get("service_name") or queued.get("service_name"),
            "action": action,
            "state_before": final.get("state_before") or queued.get("state_before"),
            "state_after": final.get("state_after"),
            "observed_state": observed.get("state") if observed else None,
            "control_allowed": observed.get("control_allowed") if observed else None,
            "error_code": final.get("error_code"),
            "message": _result_message(
                action=action,
                status=status,
                proven=proven,
                state_before=final.get("state_before") or queued.get("state_before"),
                state_after=final.get("state_after"),
                observed_state=observed.get("state") if observed else None,
                error_code=final.get("error_code"),
            ),
        }
    except ReadError as exc:
        return _safe_error(exc.code)
    except Exception:
        return _safe_error("control_unavailable")


async def _poll_until_terminal(
    client: WindowsControlClient,
    authorization: str,
    server_id: str,
    action_id: str,
) -> dict[str, Any]:
    last: dict[str, Any] = {"id": action_id, "status": "queued"}
    for _ in range(_POLL_ATTEMPTS):
        last = await client.get_action(authorization, server_id, action_id)
        if last.get("status") in _TERMINAL:
            return last
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    return {**last, "status": last.get("status") or "timeout"}


async def _observe_service(
    reader: ItPortalReader,
    authorization: str,
    server_id: str,
    service_key: str,
) -> dict[str, Any] | None:
    try:
        page = await reader.list_host_services(
            authorization,
            server_id,
            q=service_key[:120],
            present="yes",
            page=1,
            page_size=25,
        )
    except ReadError:
        return None
    items = page.get("items") if isinstance(page, dict) else None
    if not isinstance(items, list):
        return None
    key = service_key.casefold()
    for item in items:
        if isinstance(item, dict) and str(item.get("service_key") or "").casefold() == key:
            return item
    return items[0] if items and isinstance(items[0], dict) else None


def _action_label(action: str) -> str:
    return {"start": "início", "stop": "parada", "restart": "reinicialização"}.get(action, action)


def _state_label(state: str) -> str:
    return {
        "running": "em execução",
        "stopped": "parado",
        "paused": "pausado",
    }.get(state, state or "desconhecido")


def _result_message(
    *,
    action: str,
    status: str,
    proven: bool,
    state_before: str | None,
    state_after: str | None,
    observed_state: str | None,
    error_code: str | None,
) -> str:
    if proven:
        return (
            f"{_action_label(action).capitalize()} solicitada e confirmada pelo Windows. "
            f"Estado anterior: {_state_label(state_before or '')}. "
            f"Estado atual: {_state_label(state_after or observed_state or '')}."
        )
    if status == "failed":
        return (
            f"A operação não foi concluída"
            + (f" ({error_code})" if error_code else "")
            + ". Verifique o estado no servidor antes de tentar novamente."
        )
    if status == "timeout":
        return (
            "Não foi possível confirmar o resultado a tempo. "
            "Não declare sucesso; confira o estado diretamente no Windows."
        )
    return (
        "A solicitação foi aceita, mas o resultado ainda não foi comprovado. "
        f"Estado observado: {_state_label(observed_state or state_after or 'desconhecido')}."
    )
