from dataclasses import dataclass


@dataclass(frozen=True)
class ExecuteToolRequest:
    user_id: str
    access_token: str
    tool_name: str
    arguments: dict
