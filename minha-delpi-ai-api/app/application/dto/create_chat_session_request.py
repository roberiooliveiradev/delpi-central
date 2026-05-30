from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatSessionRequest:
    user_id: str
    title: str | None = None
    context: str | None = None
    project_id: str | None = None
    agent_id: str | None = None
    fork_from_session_id: str | None = None
    fork_until_message_id: str | None = None
