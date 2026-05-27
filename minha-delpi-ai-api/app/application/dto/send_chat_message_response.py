from dataclasses import dataclass


@dataclass(frozen=True)
class SendChatMessageResponse:
    messageId: str
    answer: str
    sources: list
    toolCalls: list
    canvasOpen: dict | None = None
