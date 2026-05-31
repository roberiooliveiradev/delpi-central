from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_

from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_session_memory_model import AiChatSessionMemoryModel


class PostgresChatSessionMemoryRepository(ChatSessionMemoryRepositoryPort):
    _ENTITY_KEYS = frozenset({"productCode", "branch"})
    _BEHAVIOR_KEYS = frozenset({"responseFormat", "tone"})

    def load_active_overlay(self, session_id: UUID) -> dict:
        now = datetime.now(timezone.utc)
        rows = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.active.is_(True),
            )
            .filter(
                or_(
                    AiChatSessionMemoryModel.expires_at.is_(None),
                    AiChatSessionMemoryModel.expires_at > now,
                )
            )
            .order_by(AiChatSessionMemoryModel.updated_at.desc())
            .all()
        )

        last_entities: dict[str, str] = {}
        behavior: dict[str, str] = {}

        for row in rows:
            value = row.value_json
            scalar = value if isinstance(value, str) else str(value or "").strip()

            if not scalar:
                continue

            if row.memory_type == "entity" and row.key in self._ENTITY_KEYS:
                last_entities.setdefault(row.key, scalar)
            elif row.memory_type == "behavior" and row.key in self._BEHAVIOR_KEYS:
                behavior.setdefault(row.key, scalar)

        return {
            "lastEntities": last_entities,
            "behaviorInstructions": behavior,
        }

    def sync_from_snapshot(
        self,
        session_id: UUID,
        snapshot: dict,
        *,
        source_message_id: UUID | None = None,
    ) -> None:
        if not snapshot:
            return

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30)
        entities = snapshot.get("lastEntities") or {}
        behavior = snapshot.get("behaviorInstructions") or {}

        for key, value in entities.items():
            if key not in self._ENTITY_KEYS or value in (None, "", []):
                continue

            self._upsert_row(
                session_id=session_id,
                memory_type="entity",
                key=key,
                value_json=str(value),
                source_message_id=source_message_id,
                expires_at=expires_at,
                now=now,
            )

        for key, value in behavior.items():
            if key not in self._BEHAVIOR_KEYS or value in (None, "", []):
                continue

            self._upsert_row(
                session_id=session_id,
                memory_type="behavior",
                key=key,
                value_json=str(value),
                source_message_id=source_message_id,
                expires_at=expires_at,
                now=now,
            )

    def deactivate_all(self, session_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        updated = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.active.is_(True),
            )
            .update(
                {"active": False, "updated_at": now},
                synchronize_session=False,
            )
        )
        return int(updated or 0)

    def expire_stale(self, *, older_than_days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        deactivated = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.active.is_(True),
                AiChatSessionMemoryModel.updated_at < cutoff,
            )
            .update(
                {"active": False, "updated_at": datetime.now(timezone.utc)},
                synchronize_session=False,
            )
        )
        return int(deactivated or 0)

    def _upsert_row(
        self,
        *,
        session_id: UUID,
        memory_type: str,
        key: str,
        value_json: str,
        source_message_id: UUID | None,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        existing = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == memory_type,
                AiChatSessionMemoryModel.key == key,
                AiChatSessionMemoryModel.active.is_(True),
            )
            .order_by(AiChatSessionMemoryModel.updated_at.desc())
            .first()
        )

        if existing and existing.value_json == value_json:
            existing.source_message_id = source_message_id
            existing.updated_at = now
            existing.expires_at = expires_at
            return

        if existing:
            existing.active = False
            existing.updated_at = now

        row = AiChatSessionMemoryModel(
            session_id=session_id,
            memory_type=memory_type,
            key=key,
            value_json=value_json,
            source_message_id=source_message_id,
            scope="session",
            confidence=1.0,
            active=True,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )
        db.session.add(row)
