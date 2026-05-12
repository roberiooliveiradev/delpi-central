from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChatProjectRequest:
    user_id: str
    project_id: str
    name: str | None = None
    description: str | None = None
