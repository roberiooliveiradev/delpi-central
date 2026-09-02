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
    def __init__(
        self,
        code: str,
        *,
        technical_detail: str | None = None,
        **context: Any,
    ) -> None:
        self.code = code
        self.technical_detail = technical_detail
        self.context = context
        super().__init__(technical_detail or code)


__all__ = [
    "BindingValidationError",
    "CommandNotSupportedError",
    "ContentCodedError",
    "DeviceDriverError",
    "DeviceValidationError",
]
