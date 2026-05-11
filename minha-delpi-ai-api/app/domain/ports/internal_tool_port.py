from abc import ABC, abstractmethod

from app.domain.entities.tool_result import ToolResult


class InternalToolPort(ABC):
    name: str
    description: str
    required_permission: str

    @abstractmethod
    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        raise NotImplementedError
