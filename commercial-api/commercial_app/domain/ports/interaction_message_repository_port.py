from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Mapping, Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    InteractionMention,
    InteractionMessage,
    InteractionPin,
    InteractionReaction,
)


class InteractionMessageRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, message_id: UUID) -> InteractionMessage | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_room(
        self,
        *,
        room_id: UUID,
        limit: int = 50,
        before_created_at: datetime | None = None,
        before_id: UUID | None = None,
        query: str | None = None,
    ) -> Sequence[InteractionMessage]:
        raise NotImplementedError

    @abstractmethod
    def create_message(
        self,
        *,
        room_id: UUID,
        author_user_id: str | None,
        message_kind: str,
        body_text: str,
        parent_id: UUID | None = None,
        mentions: Sequence[tuple[str, Mapping[str, object], str]] | None = None,
    ) -> InteractionMessage:
        """mentions items: (mention_kind, ref, label)."""
        raise NotImplementedError

    @abstractmethod
    def update_body(
        self,
        *,
        message_id: UUID,
        body_text: str,
    ) -> InteractionMessage | None:
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, *, message_id: UUID) -> InteractionMessage | None:
        raise NotImplementedError

    @abstractmethod
    def set_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> InteractionReaction:
        raise NotImplementedError

    @abstractmethod
    def clear_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_pins(self, room_id: UUID) -> Sequence[InteractionPin]:
        raise NotImplementedError

    @abstractmethod
    def pin_message(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        pinned_by_user_id: str,
    ) -> InteractionPin:
        raise NotImplementedError

    @abstractmethod
    def unpin_message(self, *, room_id: UUID, message_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_mentions_for_message(
        self,
        message_id: UUID,
    ) -> Sequence[InteractionMention]:
        raise NotImplementedError
