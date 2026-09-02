from __future__ import annotations

from fastapi.responses import JSONResponse

from production_pulse_app.application.services.device_poll_service import DevicePollFailedError
from production_pulse_app.core.responses import error
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    device_connectivity_http_status_code,
    device_connectivity_user_message,
)


def device_poll_failed_response(exc: DevicePollFailedError) -> JSONResponse:
    payload = error(
        device_connectivity_user_message(exc.code, fallback=exc.technical_detail),
        code=exc.code,
        status_code=device_connectivity_http_status_code(),
        details=exc.connectivity,
    )
    status_code = payload.pop("_status_code", device_connectivity_http_status_code())
    return JSONResponse(status_code=status_code, content=payload)


__all__ = ["device_poll_failed_response"]
