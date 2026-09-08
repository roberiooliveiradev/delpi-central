class AuthenticationError(Exception):
    def __init__(self, message: str = "Unauthorized"):
        self.message = message
        super().__init__(message)


class AuthorizationError(Exception):
    def __init__(self, message: str = "Forbidden"):
        self.message = message
        super().__init__(message)


class CoreApiUnavailableError(Exception):
    def __init__(self, message: str = "Authorization service unavailable"):
        self.message = message
        super().__init__(message)
