class RateLimitExceededError(Exception):
    code = "rate_limit.exceeded"

    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(message)
