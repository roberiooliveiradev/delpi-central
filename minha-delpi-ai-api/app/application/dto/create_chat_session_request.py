from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatSessionRequest:
    user_id: str
    title: str | None = None
    context: str | None = None
