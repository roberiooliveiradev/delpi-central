"""Árvore de mensagens — caminho ativo, irmãos (branches) e folha de ramo."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage


class ChatMessageBranchService:
    @classmethod
    def index_by_id(cls, messages: list[ChatMessage]) -> dict[UUID, ChatMessage]:
        return {message.id: message for message in messages}

    @classmethod
    def group_children(
        cls,
        messages: list[ChatMessage],
    ) -> dict[UUID | None, list[ChatMessage]]:
        grouped: dict[UUID | None, list[ChatMessage]] = defaultdict(list)

        for message in messages:
            grouped[message.parent_message_id].append(message)

        for children in grouped.values():
            children.sort(key=lambda item: (item.created_at, str(item.id)))

        return grouped

    @classmethod
    def build_path_to_message(
        cls,
        messages: list[ChatMessage],
        target_id: UUID | None,
    ) -> list[ChatMessage]:
        if target_id is None:
            return []

        by_id = cls.index_by_id(messages)
        path: list[ChatMessage] = []
        current: UUID | None = target_id

        while current is not None:
            message = by_id.get(current)

            if message is None:
                break

            path.append(message)
            current = message.parent_message_id

        path.reverse()
        return path

    @classmethod
    def resolve_active_leaf_id(
        cls,
        messages: list[ChatMessage],
        active_leaf_message_id: UUID | None,
    ) -> UUID | None:
        if not messages:
            return None

        by_id = cls.index_by_id(messages)

        if active_leaf_message_id is not None and active_leaf_message_id in by_id:
            return active_leaf_message_id

        return max(messages, key=lambda item: (item.created_at, str(item.id))).id

    @classmethod
    def build_active_path(
        cls,
        messages: list[ChatMessage],
        active_leaf_message_id: UUID | None,
    ) -> list[ChatMessage]:
        leaf_id = cls.resolve_active_leaf_id(messages, active_leaf_message_id)

        if leaf_id is None:
            return []

        return cls.build_path_to_message(messages, leaf_id)

    @classmethod
    def build_fork_path(
        cls,
        messages: list[ChatMessage],
        until_message_id: UUID,
        active_leaf_message_id: UUID | None = None,
    ) -> list[ChatMessage]:
        """Caminho copiado no fork — inclui resposta assistant se existir no ramo ativo."""
        path = cls.build_path_to_message(messages, until_message_id)

        if not path or path[-1].id != until_message_id:
            return path

        until_message = path[-1]

        if until_message.role != "user":
            return path

        active_path = cls.build_active_path(messages, active_leaf_message_id)

        for index, message in enumerate(active_path):
            if message.id != until_message_id:
                continue

            if index + 1 >= len(active_path):
                break

            next_message = active_path[index + 1]

            if (
                next_message.role == "assistant"
                and next_message.parent_message_id == until_message_id
            ):
                return path + [next_message]

            break

        return path

    @classmethod
    def list_user_siblings(
        cls,
        messages: list[ChatMessage],
        user_message: ChatMessage,
    ) -> list[ChatMessage]:
        siblings = [
            message
            for message in messages
            if message.role == "user"
            and message.parent_message_id == user_message.parent_message_id
        ]
        siblings.sort(key=lambda item: (item.created_at, str(item.id)))
        return siblings

    @classmethod
    def resolve_branch_leaf_id(
        cls,
        messages: list[ChatMessage],
        anchor_user_message_id: UUID,
    ) -> UUID | None:
        by_id = cls.index_by_id(messages)

        if anchor_user_message_id not in by_id:
            return None

        children_by_parent = cls.group_children(messages)
        current: UUID = anchor_user_message_id

        while True:
            children = children_by_parent.get(current, [])

            if not children:
                return current

            current = children[-1].id

    @classmethod
    def build_user_branch_navigation(
        cls,
        all_messages: list[ChatMessage],
        active_path: list[ChatMessage],
    ) -> dict[str, dict]:
        navigation: dict[str, dict] = {}

        for message in active_path:
            if message.role != "user":
                continue

            siblings = cls.list_user_siblings(all_messages, message)

            if len(siblings) <= 1:
                continue

            sibling_ids = [str(sibling.id) for sibling in siblings]
            current_index = next(
                index
                for index, sibling in enumerate(siblings)
                if sibling.id == message.id
            )

            navigation[str(message.id)] = {
                "currentIndex": current_index + 1,
                "total": len(siblings),
                "siblingIds": sibling_ids,
            }

        return navigation
