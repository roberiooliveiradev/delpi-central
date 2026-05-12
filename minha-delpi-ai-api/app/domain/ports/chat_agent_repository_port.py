from abc import ABC, abstractmethod

from app.domain.entities.chat_agent import ChatAgent


class ChatAgentRepositoryPort(ABC):
    @abstractmethod
    def list_enabled(self) -> list[ChatAgent]:
        raise NotImplementedError

    @abstractmethod
    def get_enabled_by_key(self, key: str) -> ChatAgent | None:
        raise NotImplementedError
