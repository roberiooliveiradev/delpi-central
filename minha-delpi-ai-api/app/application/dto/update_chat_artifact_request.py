from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChatArtifactRequest:
    user_id: str
    artifact_id: str
    title: str | None = None
    content: str | None = None
    metadata: dict | None = None
