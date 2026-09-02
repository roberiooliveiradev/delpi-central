from __future__ import annotations

from typing import Any


class ContentCodedError(ValueError):
    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(code)


class DeviceValidationError(ContentCodedError):
    pass


class BindingValidationError(ContentCodedError):
    pass


class CommandNotSupportedError(ContentCodedError):
    pass


class DeviceDriverError(RuntimeError):
    def __init__(self, message: str, *, code: str = "device_error") -> None:
        self.code = code
        super().__init__(message)


__all__ = [
    "BindingValidationError",
    "CommandNotSupportedError",
    "ContentCodedError",
    "DeviceDriverError",
    "DeviceValidationError",
]
