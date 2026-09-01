class DeviceValidationError(ValueError):
    pass


class DeviceDriverError(RuntimeError):
    def __init__(self, message: str, *, code: str = "device_error") -> None:
        self.code = code
        super().__init__(message)


class CommandNotSupportedError(ValueError):
    pass
