from __future__ import annotations

import asyncio
import logging
import time
from threading import Lock
from uuid import UUID

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CALLER_APP_HEADER = "X-Delpi-Caller-App"

_DEBOUNCE_SECONDS = 300
_last_sent_by_user: dict[str, float] = {}
_debounce_lock = Lock()


def _is_enabled() -> bool:
    if not settings.APP_USAGE_TRACKING_ENABLED:
        return False
    if not settings.CORE_API_BASE_URL:
        return False
    if not settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN:
        return False
    return True


def _should_record(user_id: str) -> bool:
    now = time.monotonic()
    with _debounce_lock:
        last_sent = _last_sent_by_user.get(user_id)
        if last_sent is not None and now - last_sent < _DEBOUNCE_SECONDS:
            return False
        _last_sent_by_user[user_id] = now
        return True


def _normalize_user_id(user_id: str | None) -> str | None:
    if not user_id:
        return None
    normalized = str(user_id).strip()
    if not normalized or normalized == "internal-service":
        return None
    try:
        UUID(normalized)
    except ValueError:
        return None
    return normalized


def reset_app_usage_debounce_cache() -> None:
    with _debounce_lock:
        _last_sent_by_user.clear()


def schedule_app_usage_record(
    *,
    user_id: str,
    route_path: str,
    caller_app_id: str | None = None,
) -> None:
    if not _is_enabled():
        return

    normalized_user_id = _normalize_user_id(user_id)
    if not normalized_user_id:
        return

    if not _should_record(normalized_user_id):
        return

    normalized_route = route_path.strip() or "/"
    normalized_caller = str(caller_app_id).strip() if caller_app_id else None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(
        _record_async(
            user_id=normalized_user_id,
            route_path=normalized_route,
            caller_app_id=normalized_caller,
        ),
        name="app-usage-record",
    )


async def _record_async(
    *,
    user_id: str,
    route_path: str,
    caller_app_id: str | None = None,
) -> None:
    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
    app_id = settings.APP_USAGE_APP_ID

    payload = {
        "appId": app_id,
        "userId": user_id,
        "routePath": route_path,
    }

    headers = {"Authorization": f"Bearer {token}"}
    if caller_app_id:
        headers[CALLER_APP_HEADER] = caller_app_id

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{base_url}/integrations/app-usage/record",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            logger.debug(
                "app_usage_record_rejected status=%s app_id=%s user_id=%s",
                response.status_code,
                app_id,
                user_id,
            )
    except Exception:
        logger.debug(
            "app_usage_record_failed app_id=%s user_id=%s",
            app_id,
            user_id,
            exc_info=True,
        )
