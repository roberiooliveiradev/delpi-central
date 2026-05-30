from __future__ import annotations

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import is_public_path
from delpi_auth.service_token import request_has_valid_internal_service_token

from app.application.services.app_usage_tracker import schedule_app_usage_record


def _normalize_route_path(path: str) -> str:
    normalized = path.split("?", 1)[0] or "/"
    root_path = "/apps/api-delpi"
    if normalized.startswith(root_path):
        suffix = normalized[len(root_path) :] or "/"
        return suffix if suffix.startswith("/") else f"/{suffix}"
    return normalized


async def app_usage_tracking_middleware(request: Request, call_next):
    response = await call_next(request)

    if request.method.upper() == "OPTIONS":
        return response

    if is_public_path(request.url.path):
        return response

    if request_has_valid_internal_service_token(request):
        return response

    if response.status_code >= 400:
        return response

    user = getattr(request.state, "user", None)
    user_id = getattr(user, "id", None) if user is not None else None

    raw_caller = request.headers.get("X-Delpi-Caller-App")
    caller_app_id = raw_caller.strip() if isinstance(raw_caller, str) and raw_caller.strip() else None

    schedule_app_usage_record(
        user_id=str(user_id) if user_id is not None else "",
        route_path=_normalize_route_path(request.url.path),
        caller_app_id=caller_app_id,
    )

    return response
