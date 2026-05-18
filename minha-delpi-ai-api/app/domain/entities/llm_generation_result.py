from dataclasses import dataclass, field


@dataclass(frozen=True)
class LlmToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class LlmGenerationResult:
    content: str
    tool_calls: list[LlmToolCall] = field(default_factory=list)
