class ChatInputSecurityError(Exception):
    code = "security.input_blocked"

    def __init__(
        self,
        message: str = "Message blocked by security policy",
        *,
        flags: list[str] | None = None,
        risk_score: float | None = None,
    ):
        self.message = message
        self.flags = flags or []
        self.risk_score = risk_score
        super().__init__(message)
