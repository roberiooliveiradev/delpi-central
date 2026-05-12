from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatProjectRequest:
    user_id: str
    name: str
    description: str | None = None
