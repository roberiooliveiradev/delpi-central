from __future__ import annotations

from uuid import UUID

from app.domain.ports.chat_project_peer_context_repository_port import (
    ChatProjectPeerContextRepositoryPort,
    PeerMemoryRecord,
    PeerMessageRecord,
    PeerSessionRecord,
)
from app.extensions.db import db
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_memory_model import AiChatSessionMemoryModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class PostgresChatProjectPeerContextRepository(ChatProjectPeerContextRepositoryPort):
    def list_peer_sessions(
        self,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
        user_id: UUID,
        limit: int,
    ) -> list[PeerSessionRecord]:
        rows = (
            AiChatSessionModel.query.filter(
                AiChatSessionModel.project_id == project_id,
                AiChatSessionModel.user_id == user_id,
                AiChatSessionModel.id != exclude_session_id,
                AiChatSessionModel.archived_at.is_(None),
            )
            .order_by(AiChatSessionModel.updated_at.desc())
            .limit(max(1, limit))
            .all()
        )

        return [
            PeerSessionRecord(id=row.id, title=str(row.title or "").strip() or None)
            for row in rows
        ]

    def list_recent_messages(
        self,
        session_id: UUID,
        *,
        limit: int,
    ) -> list[PeerMessageRecord]:
        rows = (
            AiChatMessageModel.query.filter(
                AiChatMessageModel.session_id == session_id,
            )
            .order_by(AiChatMessageModel.created_at.desc())
            .limit(max(1, limit))
            .all()
        )

        return [
            PeerMessageRecord(
                role=str(row.role or "").strip(),
                content=str(row.content or "").strip(),
                message_metadata=(
                    dict(row.message_metadata)
                    if isinstance(row.message_metadata, dict)
                    else None
                ),
            )
            for row in reversed(rows)
        ]

    def list_peer_session_ids(
        self,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
        limit: int,
    ) -> list[UUID]:
        return [
            row[0]
            for row in db.session.query(AiChatSessionModel.id)
            .filter(
                AiChatSessionModel.project_id == project_id,
                AiChatSessionModel.id != exclude_session_id,
                AiChatSessionModel.archived_at.is_(None),
            )
            .order_by(AiChatSessionModel.updated_at.desc())
            .limit(max(1, limit))
            .all()
        ]

    def list_active_peer_memories(
        self,
        session_ids: list[UUID],
    ) -> list[PeerMemoryRecord]:
        if not session_ids:
            return []

        rows = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id.in_(session_ids),
                AiChatSessionMemoryModel.active.is_(True),
            )
            .order_by(AiChatSessionMemoryModel.updated_at.desc())
            .all()
        )

        return [
            PeerMemoryRecord(
                memory_type=str(row.memory_type or "").strip(),
                key=str(row.key or "").strip(),
                value_json=row.value_json,
            )
            for row in rows
        ]
