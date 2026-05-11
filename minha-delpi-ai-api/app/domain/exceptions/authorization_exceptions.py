class AuthorizationError(Exception):
    code = "forbidden"
    message = "Permission denied"


class MissingPermissionError(AuthorizationError):
    code = "forbidden"

    def __init__(self, permission: str):
        self.permission = permission
        self.message = f"Missing required permission: {permission}"
        super().__init__(self.message)


class CoreApiUnavailableError(Exception):
    code = "core_api.unavailable"
    message = "Core API unavailable"
