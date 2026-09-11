"""Fan-out de eventos leves para o hub WebSocket do Production Pulse."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any
from uuid import UUID

from production_pulse_app.application.services.production_pulse_realtime_hub import (
    production_pulse_realtime_hub,
)
from production_pulse_app.config import settings

logger = logging.getLogger(__name__)

# Progress/status floods: at most one ota.target.updated per target per second
# unless status changes or progress jumps by >= 5pp.
_TARGET_THROTTLE_SECONDS = 1.0
_TARGET_PROGRESS_STEP = 5
_POLL_DEVICE_THROTTLE_SECONDS = 15.0

_lock = threading.Lock()
_last_target_emit: dict[str, tuple[float, str, int | None]] = {}
_last_poll_device_emit: dict[str, float] = {}


def safe_realtime(fn, **kwargs) -> None:
    """Persist-before-publish: never fail the writer if fan-out breaks."""
    try:
        fn(**kwargs)
    except Exception:  # noqa: BLE001
        logger.exception("production_pulse_realtime_notify_failed")


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def branch_room(branch: str) -> str:
    code = str(branch or "").strip()
    return f"branch:{code}"


def device_room(device_id: str | UUID) -> str:
    return f"device:{str(device_id).strip()}"


def ota_job_room(job_id: str | UUID) -> str:
    return f"ota.job:{str(job_id).strip()}"


def _realtime_enabled() -> bool:
    return bool(settings.PP_REALTIME_ENABLED)


def _broadcast_rooms(room_keys: list[str], payload: dict[str, Any]) -> None:
    if not _realtime_enabled():
        return
    try:
        production_pulse_realtime_hub.schedule_broadcast_rooms(room_keys, payload)
    except Exception:  # noqa: BLE001
        logger.exception("production_pulse_realtime_schedule_failed rooms=%s", room_keys)


def _unique_rooms(*candidates: str | None) -> list[str]:
    seen: set[str] = set()
    rooms: list[str] = []
    for raw in candidates:
        key = str(raw or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        rooms.append(key)
    return rooms


def _branch_rooms(*branches: str | None) -> list[str]:
    rooms: list[str] = []
    for branch in branches:
        code = str(branch or "").strip()
        if code in {"01", "02"}:
            rooms.append(branch_room(code))
    return rooms


def notify_device_updated(
    *,
    reason: str,
    device_id: str | UUID,
    branch: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "device.updated",
        "reason": reason,
        "deviceId": str(device_id),
        "branch": (branch or "").strip() or None,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorClientId": (actor_client_id or "").strip() or None,
    }
    rooms = _unique_rooms(
        *_branch_rooms(branch),
        device_room(device_id),
    )
    if not rooms and branch in {"01", "02"}:
        rooms = [branch_room(str(branch))]
    if not rooms:
        # Still fan-out to both branches if unknown (rare hard-delete edge).
        rooms = [branch_room("01"), branch_room("02")]
    _broadcast_rooms(rooms, payload)


def notify_device_updated_from_poll(
    *,
    device_id: str | UUID,
    branch: str | None = None,
) -> None:
    """Throttled hint when poll changes presence/telemetry-facing fields."""
    key = str(device_id)
    now = time.monotonic()
    with _lock:
        last = _last_poll_device_emit.get(key, 0.0)
        if now - last < _POLL_DEVICE_THROTTLE_SECONDS:
            return
        _last_poll_device_emit[key] = now
    notify_device_updated(
        reason="poll",
        device_id=device_id,
        branch=branch,
    )


def notify_firmware_catalog_updated(
    *,
    reason: str,
    firmware_id: str | UUID | None = None,
    firmware_key: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "firmware.catalog.updated",
        "reason": reason,
        "firmwareId": str(firmware_id) if firmware_id else None,
        "firmwareKey": (firmware_key or "").strip() or None,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorClientId": (actor_client_id or "").strip() or None,
    }
    _broadcast_rooms([branch_room("01"), branch_room("02")], payload)


def notify_ota_job_updated(
    *,
    reason: str,
    job_id: str | UUID,
    branch: str | None = None,
    status: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "ota.job.updated",
        "reason": reason,
        "jobId": str(job_id),
        "branch": (branch or "").strip() or None,
        "status": (status or "").strip() or None,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorClientId": (actor_client_id or "").strip() or None,
    }
    rooms = _unique_rooms(
        *_branch_rooms(branch),
        ota_job_room(job_id),
    )
    if not rooms:
        rooms = [branch_room("01"), branch_room("02"), ota_job_room(job_id)]
    _broadcast_rooms(rooms, payload)


def notify_ota_target_updated(
    *,
    reason: str,
    target_id: str | UUID,
    job_id: str | UUID,
    device_id: str | UUID,
    branch: str | None = None,
    status: str | None = None,
    progress_percent: int | None = None,
    force: bool = False,
) -> None:
    status_norm = (status or "").strip().lower() or None
    pct: int | None = None
    if progress_percent is not None:
        try:
            pct = max(0, min(100, int(progress_percent)))
        except (TypeError, ValueError):
            pct = None

    key = str(target_id)
    now = time.monotonic()
    with _lock:
        last = _last_target_emit.get(key)
        if not force and last is not None:
            last_ts, last_status, last_pct = last
            status_changed = last_status != (status_norm or "")
            pct_jump = (
                pct is not None
                and last_pct is not None
                and abs(pct - last_pct) >= _TARGET_PROGRESS_STEP
            )
            pct_first = pct is not None and last_pct is None
            timed_out = (now - last_ts) >= _TARGET_THROTTLE_SECONDS
            if not (status_changed or pct_jump or pct_first or timed_out):
                return
        _last_target_emit[key] = (now, status_norm or "", pct)

    payload: dict[str, Any] = {
        "type": "ota.target.updated",
        "reason": reason,
        "targetId": str(target_id),
        "jobId": str(job_id),
        "deviceId": str(device_id),
        "branch": (branch or "").strip() or None,
        "status": status_norm,
        "progressPercent": pct,
    }
    rooms = _unique_rooms(
        *_branch_rooms(branch),
        ota_job_room(job_id),
        device_room(device_id),
    )
    if not rooms:
        rooms = [
            branch_room("01"),
            branch_room("02"),
            ota_job_room(job_id),
            device_room(device_id),
        ]
    _broadcast_rooms(rooms, payload)
