from dataclasses import dataclass


@dataclass(frozen=True)
class ExecuteToolResponse:
    name: str
    data: dict | list
    metadata: dict | None
