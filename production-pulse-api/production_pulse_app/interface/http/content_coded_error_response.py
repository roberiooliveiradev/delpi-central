from __future__ import annotations

from fastapi.responses import JSONResponse

from production_pulse_app.core.responses import error
from production_pulse_app.domain.errors import (
    BindingValidationError,
    CommandNotSupportedError,
    ContentCodedError,
    DeviceValidationError,
)
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    command_error_message,
    validation_error_message,
)


def resolve_content_coded_message(exc: ContentCodedError) -> str:
    params = dict(exc.params)
    if isinstance(exc, CommandNotSupportedError):
        return command_error_message(exc.code, **params)
    return validation_error_message(exc.code, **params)


def content_coded_error_response(
    exc: ContentCodedError,
    *,
    status_code: int = 422,
) -> JSONResponse:
    payload = error(
        resolve_content_coded_message(exc),
        code=exc.code,
        status_code=status_code,
    )
    resolved_status = payload.pop("_status_code", status_code)
    return JSONResponse(status_code=resolved_status, content=payload)


__all__ = [
    "BindingValidationError",
    "CommandNotSupportedError",
    "ContentCodedError",
    "DeviceValidationError",
    "content_coded_error_response",
    "resolve_content_coded_message",
]
