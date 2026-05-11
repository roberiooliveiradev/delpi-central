from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    name: str
    data: dict | list
    metadata: dict | None = None
