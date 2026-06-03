from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_

from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_session_memory_model import AiChatSessionMemoryModel


class PostgresChatSessionMemoryRepository(ChatSessionMemoryRepositoryPort):
    _ENTITY_KEYS = frozenset({"productCode", "branch", "warehouse", "period"})
    _BEHAVIOR_KEYS = frozenset(
        {
            "responseFormat",
            "tone",
            "answerLength",
            "emailWriting",
            "textCorrection",
            "scope",
            "finalVersionOnly",
            "interactivityUsage",
        }
    )

    def load_active_overlay(self, session_id: UUID) -> dict:
        if self._has_clear_marker(session_id):
            return {"lastEntities": {}, "behaviorInstructions": {}, "cleared": True}

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
            "userContextItems": self.list_context_items(session_id),
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
        self._clear_clear_marker(session_id, now=now)
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
        self._set_clear_marker(session_id, now=now)
        return int(updated or 0)

    def upsert_entity(
        self,
        session_id: UUID,
        key: str,
        value: str,
        *,
        source_message_id: UUID | None = None,
    ) -> None:
        if key not in self._ENTITY_KEYS or not str(value or "").strip():
            return

        now = datetime.now(timezone.utc)
        self._clear_clear_marker(session_id, now=now)
        self._upsert_row(
            session_id=session_id,
            memory_type="entity",
            key=key,
            value_json=str(value).strip(),
            source_message_id=source_message_id,
            expires_at=now + timedelta(days=30),
            now=now,
        )

    def list_context_items(self, session_id: UUID) -> list[dict]:
        if self._has_clear_marker(session_id):
            return []

        now = datetime.now(timezone.utc)
        rows = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == "context_item",
                AiChatSessionMemoryModel.active.is_(True),
            )
            .filter(
                or_(
                    AiChatSessionMemoryModel.expires_at.is_(None),
                    AiChatSessionMemoryModel.expires_at > now,
                )
            )
            .order_by(AiChatSessionMemoryModel.created_at.asc())
            .limit(24)
            .all()
        )

        items: list[dict] = []

        for row in rows:
            payload = row.value_json

            if isinstance(payload, dict) and payload.get("id"):
                items.append(payload)

        return items[-12:]

    def add_context_item(self, session_id: UUID, item: dict) -> dict:
        item_id = str(item.get("id") or "").strip()

        if not item_id:
            raise ValueError("Context item id is required.")

        now = datetime.now(timezone.utc)
        self._clear_clear_marker(session_id, now=now)
        self._upsert_row(
            session_id=session_id,
            memory_type="context_item",
            key=item_id[:64],
            value_json=item,
            source_message_id=None,
            expires_at=now + timedelta(days=30),
            now=now,
        )

        return item

    def remove_context_item(self, session_id: UUID, item_id: str) -> bool:
        token = str(item_id or "").strip()

        if not token:
            return False

        now = datetime.now(timezone.utc)
        updated = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == "context_item",
                AiChatSessionMemoryModel.key == token[:64],
                AiChatSessionMemoryModel.active.is_(True),
            )
            .update(
                {"active": False, "updated_at": now},
                synchronize_session=False,
            )
        )

        if int(updated or 0) > 0:
            return True

        rows = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == "context_item",
                AiChatSessionMemoryModel.active.is_(True),
            )
            .filter(
                or_(
                    AiChatSessionMemoryModel.expires_at.is_(None),
                    AiChatSessionMemoryModel.expires_at > now,
                )
            )
            .all()
        )

        for row in rows:
            payload = row.value_json

            if not isinstance(payload, dict):
                continue

            payload_id = str(payload.get("id") or "").strip()
            message_id = str(payload.get("messageId") or "").strip()
            kind = str(payload.get("kind") or "").strip().lower()
            stable = f"msg:{message_id}:{kind}" if message_id and kind else ""

            if payload_id != token and stable != token:
                continue

            row.active = False
            row.updated_at = now
            return True

        return False

    def deactivate_entity(self, session_id: UUID, key: str) -> bool:
        if key not in self._ENTITY_KEYS:
            return False

        now = datetime.now(timezone.utc)
        updated = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == "entity",
                AiChatSessionMemoryModel.key == key,
                AiChatSessionMemoryModel.active.is_(True),
            )
            .update(
                {"active": False, "updated_at": now},
                synchronize_session=False,
            )
        )
        return int(updated or 0) > 0

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

    def _has_clear_marker(self, session_id: UUID) -> bool:
        return (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id == session_id,
                AiChatSessionMemoryModel.memory_type == "meta",
                AiChatSessionMemoryModel.key == "cleared",
                AiChatSessionMemoryModel.active.is_(True),
            ).first()
            is not None
        )

    def _set_clear_marker(self, session_id: UUID, *, now: datetime) -> None:
        for row in AiChatSessionMemoryModel.query.filter(
            AiChatSessionMemoryModel.session_id == session_id,
            AiChatSessionMemoryModel.memory_type == "meta",
            AiChatSessionMemoryModel.key == "cleared",
            AiChatSessionMemoryModel.active.is_(True),
        ):
            row.active = False
            row.updated_at = now

        db.session.add(
            AiChatSessionMemoryModel(
                session_id=session_id,
                memory_type="meta",
                key="cleared",
                value_json="true",
                scope="session",
                active=True,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(hours=24),
            )
        )

    def _clear_clear_marker(self, session_id: UUID, *, now: datetime) -> None:
        AiChatSessionMemoryModel.query.filter(
            AiChatSessionMemoryModel.session_id == session_id,
            AiChatSessionMemoryModel.memory_type == "meta",
            AiChatSessionMemoryModel.key == "cleared",
            AiChatSessionMemoryModel.active.is_(True),
        ).update(
            {"active": False, "updated_at": now},
            synchronize_session=False,
        )

    def _upsert_row(
        self,
        *,
        session_id: UUID,
        memory_type: str,
        key: str,
        value_json: str | dict,
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
