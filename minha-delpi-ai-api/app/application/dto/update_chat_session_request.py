from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChatSessionRequest:
    user_id: str
    session_id: str
    title: str | None = None
    update_title: bool = False
    project_id: str | None = None
    update_project_id: bool = False
