from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    InteractionMention,
    InteractionMessage,
    InteractionPin,
    InteractionReaction,
)
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_MESSAGE_COLUMNS = """
    id, room_id, parent_id, author_user_id, message_kind, body_text,
    edited_at, deleted_at, created_at
"""

_MENTION_COLUMNS = "id, message_id, mention_kind, ref, label"
_REACTION_COLUMNS = "message_id, user_id, code, created_at"
_PIN_COLUMNS = "id, room_id, message_id, pinned_by_user_id, created_at"


def _as_ref(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _row_mention(row: dict[str, Any] | None) -> InteractionMention | None:
    if not row:
        return None
    return InteractionMention(
        id=row["id"],
        message_id=row["message_id"],
        mention_kind=row["mention_kind"],
        ref=_as_ref(row.get("ref")),
        label=row["label"],
    )


def _row_reaction(row: dict[str, Any] | None) -> InteractionReaction | None:
    if not row:
        return None
    return InteractionReaction(
        message_id=row["message_id"],
        user_id=row["user_id"],
        code=row["code"],
        created_at=row["created_at"],
    )


def _row_pin(row: dict[str, Any] | None) -> InteractionPin | None:
    if not row:
        return None
    return InteractionPin(
        id=row["id"],
        room_id=row["room_id"],
        message_id=row["message_id"],
        pinned_by_user_id=row["pinned_by_user_id"],
        created_at=row["created_at"],
    )


def _row_message_base(row: dict[str, Any] | None) -> InteractionMessage | None:
    if not row:
        return None
    return InteractionMessage(
        id=row["id"],
        room_id=row["room_id"],
        parent_id=row.get("parent_id"),
        author_user_id=row.get("author_user_id"),
        message_kind=row["message_kind"],
        body_text=row["body_text"] or "",
        edited_at=row.get("edited_at"),
        deleted_at=row.get("deleted_at"),
        created_at=row["created_at"],
    )


class PostgresInteractionMessageRepository(
    PluginBaseRepository,
    InteractionMessageRepositoryPort,
):
    def _load_mentions(
        self,
        message_ids: Sequence[UUID | str],
    ) -> dict[str, list[InteractionMention]]:
        ids = [str(item) for item in message_ids if item]
        if not ids:
            return {}
        rows = self.fetch_all(
            f"""
            SELECT {_MENTION_COLUMNS}
              FROM commercial.interaction_mentions
             WHERE message_id = ANY(%s)
             ORDER BY id ASC
            """,
            (ids,),
        )
        out: dict[str, list[InteractionMention]] = {}
        for row in rows:
            mention = _row_mention(row)
            if mention is None:
                continue
            out.setdefault(str(mention.message_id), []).append(mention)
        return out

    def _load_reactions(
        self,
        message_ids: Sequence[UUID | str],
    ) -> dict[str, list[InteractionReaction]]:
        ids = [str(item) for item in message_ids if item]
        if not ids:
            return {}
        rows = self.fetch_all(
            f"""
            SELECT {_REACTION_COLUMNS}
              FROM commercial.interaction_reactions
             WHERE message_id = ANY(%s)
             ORDER BY created_at ASC
            """,
            (ids,),
        )
        out: dict[str, list[InteractionReaction]] = {}
        for row in rows:
            reaction = _row_reaction(row)
            if reaction is None:
                continue
            out.setdefault(str(reaction.message_id), []).append(reaction)
        return out

    def _hydrate(
        self,
        messages: Sequence[InteractionMessage],
    ) -> list[InteractionMessage]:
        if not messages:
            return []
        ids = [item.id for item in messages]
        mentions = self._load_mentions(ids)
        reactions = self._load_reactions(ids)
        hydrated: list[InteractionMessage] = []
        for message in messages:
            key = str(message.id)
            hydrated.append(
                InteractionMessage(
                    id=message.id,
                    room_id=message.room_id,
                    parent_id=message.parent_id,
                    author_user_id=message.author_user_id,
                    message_kind=message.message_kind,
                    body_text=message.body_text,
                    edited_at=message.edited_at,
                    deleted_at=message.deleted_at,
                    created_at=message.created_at,
                    mentions=tuple(mentions.get(key, ())),
                    reactions=tuple(reactions.get(key, ())),
                )
            )
        return hydrated

    def get_by_id(self, message_id: UUID) -> InteractionMessage | None:
        row = self.fetch_one(
            f"""
            SELECT {_MESSAGE_COLUMNS}
              FROM commercial.interaction_messages
             WHERE id = %s
            """,
            (str(message_id),),
        )
        base = _row_message_base(row)
        if base is None:
            return None
        return self._hydrate([base])[0]

    def list_for_room(
        self,
        *,
        room_id: UUID,
        limit: int = 50,
        before_created_at: datetime | None = None,
        before_id: UUID | None = None,
        query: str | None = None,
    ) -> Sequence[InteractionMessage]:
        caps = max(1, min(int(limit), 200))
        params: list[Any] = [str(room_id)]
        filters = [
            "room_id = %s",
            "deleted_at IS NULL",
        ]
        q = (query or "").strip()
        if q:
            filters.append("body_text ILIKE %s")
            params.append(f"%{q}%")
        if before_created_at is not None and before_id is not None:
            filters.append("(created_at, id) < (%s, %s)")
            params.extend([before_created_at, str(before_id)])
        elif before_created_at is not None:
            filters.append("created_at < %s")
            params.append(before_created_at)
        params.append(caps)
        where_sql = " AND ".join(filters)
        rows = self.fetch_all(
            f"""
            SELECT {_MESSAGE_COLUMNS}
              FROM commercial.interaction_messages
             WHERE {where_sql}
             ORDER BY created_at DESC, id DESC
             LIMIT %s
            """,
            tuple(params),
        )
        bases = [msg for row in rows if (msg := _row_message_base(row)) is not None]
        return self._hydrate(bases)

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
        with self.db():
            row = self.execute_returning_one(
                f"""
                INSERT INTO commercial.interaction_messages (
                    room_id, parent_id, author_user_id, message_kind, body_text
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING {_MESSAGE_COLUMNS}
                """,
                (
                    str(room_id),
                    str(parent_id) if parent_id else None,
                    (author_user_id or "").strip() or None,
                    message_kind.strip(),
                    body_text or "",
                ),
                auto_commit=False,
            )
            base = _row_message_base(row)
            if base is None:
                self.rollback()
                raise RuntimeError("Falha ao criar mensagem da sala.")
            try:
                for kind, ref, label in mentions or ():
                    mention_kind = str(kind or "").strip()
                    mention_label = str(label or "").strip()
                    if not mention_kind or not mention_label:
                        continue
                    self.execute(
                        f"""
                        INSERT INTO commercial.interaction_mentions (
                            message_id, mention_kind, ref, label
                        ) VALUES (%s, %s, %s::jsonb, %s)
                        """,
                        (
                            str(base.id),
                            mention_kind,
                            json.dumps(dict(ref)),
                            mention_label,
                        ),
                        auto_commit=False,
                    )
                self.execute(
                    """
                    UPDATE commercial.interaction_rooms
                       SET updated_at = NOW()
                     WHERE id = %s
                       AND deleted_at IS NULL
                    """,
                    (str(room_id),),
                    auto_commit=False,
                )
                self.commit()
            except Exception:
                self.rollback()
                raise
            return self.get_by_id(base.id) or base

    def update_body(
        self,
        *,
        message_id: UUID,
        body_text: str,
    ) -> InteractionMessage | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.interaction_messages
               SET body_text = %s,
                   edited_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
               AND message_kind = 'text'
         RETURNING {_MESSAGE_COLUMNS}
            """,
            (body_text or "", str(message_id)),
        )
        base = _row_message_base(row)
        if base is None:
            return None
        return self._hydrate([base])[0]

    def soft_delete(self, *, message_id: UUID) -> InteractionMessage | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.interaction_messages
               SET deleted_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
         RETURNING {_MESSAGE_COLUMNS}
            """,
            (str(message_id),),
        )
        base = _row_message_base(row)
        if base is None:
            return None
        return self._hydrate([base])[0]

    def set_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> InteractionReaction:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.interaction_reactions (message_id, user_id, code)
            VALUES (%s, %s, %s)
            ON CONFLICT (message_id, user_id, code) DO UPDATE
               SET created_at = commercial.interaction_reactions.created_at
         RETURNING {_REACTION_COLUMNS}
            """,
            (str(message_id), user_id.strip(), code.strip()),
        )
        reaction = _row_reaction(row)
        if reaction is None:
            raise RuntimeError("Falha ao gravar reação.")
        return reaction

    def clear_reaction(
        self,
        *,
        message_id: UUID,
        user_id: str,
        code: str,
    ) -> bool:
        row = self.execute_returning_one(
            """
            DELETE FROM commercial.interaction_reactions
             WHERE message_id = %s
               AND user_id = %s
               AND code = %s
         RETURNING message_id
            """,
            (str(message_id), user_id.strip(), code.strip()),
        )
        return row is not None

    def list_pins(self, room_id: UUID) -> Sequence[InteractionPin]:
        rows = self.fetch_all(
            f"""
            SELECT {_PIN_COLUMNS}
              FROM commercial.interaction_pins
             WHERE room_id = %s
             ORDER BY created_at DESC
            """,
            (str(room_id),),
        )
        return [pin for row in rows if (pin := _row_pin(row)) is not None]

    def pin_message(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        pinned_by_user_id: str,
    ) -> InteractionPin:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.interaction_pins (
                room_id, message_id, pinned_by_user_id
            ) VALUES (%s, %s, %s)
            ON CONFLICT (room_id, message_id) DO UPDATE
               SET pinned_by_user_id = EXCLUDED.pinned_by_user_id
         RETURNING {_PIN_COLUMNS}
            """,
            (str(room_id), str(message_id), pinned_by_user_id.strip()),
        )
        pin = _row_pin(row)
        if pin is None:
            raise RuntimeError("Falha ao fixar mensagem.")
        return pin

    def unpin_message(self, *, room_id: UUID, message_id: UUID) -> bool:
        row = self.execute_returning_one(
            """
            DELETE FROM commercial.interaction_pins
             WHERE room_id = %s
               AND message_id = %s
         RETURNING id
            """,
            (str(room_id), str(message_id)),
        )
        return row is not None

    def list_mentions_for_message(
        self,
        message_id: UUID,
    ) -> Sequence[InteractionMention]:
        return tuple(self._load_mentions([message_id]).get(str(message_id), ()))
