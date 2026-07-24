from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from tm_app.core.serialize import json_safe
from tm_app.infrastructure.persistence.repositories.collaboration_presence_repository import (
    ALLOWED_ENTITY_TYPES,
    LOCK_TTL_SECONDS,
    CollaborationPresenceRepository,
)

# Salas `catalog:<id>` (dashboard, processo, filial…) só fazem fan-out WS.
# A coluna collaboration_presence.entity_id é UUID — nunca persistir nestas salas.
PRESENCE_LESS_ENTITY_TYPES = frozenset({"catalog"})


class CollaborationPresenceService:
    def __init__(self, repo: CollaborationPresenceRepository | None = None) -> None:
        self._repo = repo or CollaborationPresenceRepository()

    def list_presence(self, *, entity_type: str, entity_id: str) -> dict[str, Any]:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            return self._empty_presence(entity_type, entity_id)
        self._repo.purge_stale()
        rows = self._repo.list_active(entity_type=entity_type, entity_id=entity_id)
        viewers: list[dict[str, Any]] = []
        editors: list[dict[str, Any]] = []
        for row in rows:
            item = self._serialize_row(row)
            if item["mode"] == "editing" and item.get("lock_active"):
                editors.append(item)
            else:
                viewers.append(item)
        return json_safe(
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "viewers": viewers,
                "editors": editors,
            }
        )

    def heartbeat(
        self,
        *,
        entity_type: str,
        entity_id: str,
        section_key: str,
        user_id: str,
        user_name: str | None,
        user_email: str | None,
        mode: str = "viewing",
    ) -> dict[str, Any]:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            return {
                "user_id": user_id,
                "user_name": user_name or user_email,
                "user_email": user_email,
                "section_key": section_key or "",
                "mode": "viewing",
                "lock_active": False,
                "heartbeat_at": None,
            }
        if mode not in {"viewing", "editing"}:
            mode = "viewing"
        lock_expires = None
        if mode == "editing":
            lock_expires = datetime.now(timezone.utc) + timedelta(seconds=LOCK_TTL_SECONDS)
        row = self._repo.upsert_presence(
            entity_type=entity_type,
            entity_id=entity_id,
            section_key=section_key or "",
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            mode=mode,
            lock_expires_at=lock_expires,
        )
        return self._serialize_row(row)

    def acquire_lock(
        self,
        *,
        entity_type: str,
        entity_id: str,
        section_key: str,
        user_id: str,
        user_name: str | None,
        user_email: str | None,
    ) -> dict[str, Any]:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            raise ValueError(
                "Travas colaborativas não se aplicam a salas de catálogo/listagem."
            )
        self._repo.purge_stale()
        holder = self._repo.get_active_lock_holder(
            entity_type=entity_type,
            entity_id=entity_id,
            section_key=section_key or "",
            exclude_user_id=user_id,
        )
        if holder:
            return {
                "acquired": False,
                "holder": {
                    "user_id": holder.get("user_id"),
                    "user_name": holder.get("user_name") or holder.get("user_email"),
                    "section_key": holder.get("section_key"),
                },
            }
        row = self._repo.upsert_presence(
            entity_type=entity_type,
            entity_id=entity_id,
            section_key=section_key or "",
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            mode="editing",
            lock_expires_at=datetime.now(timezone.utc) + timedelta(seconds=LOCK_TTL_SECONDS),
        )
        return {"acquired": True, "presence": self._serialize_row(row)}

    def release_lock(
        self,
        *,
        entity_type: str,
        entity_id: str,
        section_key: str,
        user_id: str,
    ) -> None:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            return
        self._repo.release_user_locks(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            section_key=section_key or "",
        )

    def release_all(self, *, entity_type: str, entity_id: str, user_id: str) -> None:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            return
        self._repo.release_user_locks(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
        )

    def clear_user_presence(self, *, entity_type: str, entity_id: str, user_id: str) -> None:
        self._assert_entity(entity_type)
        if not self._uses_db_presence(entity_type, entity_id):
            return
        self._repo.release_user_locks(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
        )
        self._repo.delete_user_presence(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
        )

    @staticmethod
    def _assert_entity(entity_type: str) -> None:
        if entity_type not in ALLOWED_ENTITY_TYPES:
            raise ValueError(f"entity_type inválido: {entity_type}")

    @staticmethod
    def _uses_db_presence(entity_type: str, entity_id: str) -> bool:
        """Presença/locks no Postgres só para entidades com entity_id UUID."""
        if entity_type in PRESENCE_LESS_ENTITY_TYPES:
            return False
        try:
            UUID(str(entity_id))
        except (TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _empty_presence(entity_type: str, entity_id: str) -> dict[str, Any]:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "viewers": [],
            "editors": [],
        }

    @staticmethod
    def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
        lock_expires = row.get("lock_expires_at")
        lock_active = False
        if lock_expires is not None:
            if hasattr(lock_expires, "tzinfo") and lock_expires.tzinfo is None:
                lock_expires = lock_expires.replace(tzinfo=timezone.utc)
            lock_active = lock_expires > datetime.now(timezone.utc)
        return json_safe(
            {
                "user_id": row.get("user_id"),
                "user_name": row.get("user_name") or row.get("user_email"),
                "user_email": row.get("user_email"),
                "section_key": row.get("section_key") or "",
                "mode": row.get("mode") or "viewing",
                "lock_active": lock_active,
                "heartbeat_at": row.get("heartbeat_at"),
            }
        )
