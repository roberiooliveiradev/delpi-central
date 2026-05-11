from dataclasses import dataclass


@dataclass(frozen=True)
class SendChatMessageRequest:
    user_id: str
    session_id: str
    message: str
    context: str | None = None
    access_token: str | None = None
