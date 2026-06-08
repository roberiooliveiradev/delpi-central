from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class PeerSessionRecord:
    id: UUID
    title: str | None


@dataclass(frozen=True)
class PeerMessageRecord:
    role: str
    content: str
    message_metadata: dict[str, Any] | None


@dataclass(frozen=True)
class PeerMemoryRecord:
    memory_type: str
    key: str
    value_json: Any


class ChatProjectPeerContextRepositoryPort(ABC):
    @abstractmethod
    def list_peer_sessions(
        self,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
        user_id: UUID,
        limit: int,
    ) -> list[PeerSessionRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_messages(
        self,
        session_id: UUID,
        *,
        limit: int,
    ) -> list[PeerMessageRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_peer_session_ids(
        self,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
        limit: int,
    ) -> list[UUID]:
        raise NotImplementedError

    @abstractmethod
    def list_active_peer_memories(
        self,
        session_ids: list[UUID],
    ) -> list[PeerMemoryRecord]:
        raise NotImplementedError
