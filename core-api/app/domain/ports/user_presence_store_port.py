# app/domain/ports/user_presence_store_port.py

from typing import Protocol

from app.domain.dto.user_presence_dto import UserPresenceSummaryDTO


class UserPresenceStorePort(Protocol):

    def register(self, *, user_id: str, session_id: str) -> None:
        ...

    def unregister(self, session_id: str) -> None:
        ...

    def touch(self, session_id: str) -> None:
        ...

    def list_online(self) -> list[UserPresenceSummaryDTO]:
        ...
