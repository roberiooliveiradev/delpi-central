from __future__ import annotations

from typing import Any

from psycopg.errors import UniqueViolation

from app.domain.services.mural_acessos.exceptions import MuralAcessosValidationError
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_HUB_COLUMNS = """
    id, title, subtitle, public_token, created_at, updated_at
"""

_LINK_COLUMNS = """
    id, hub_id, title, url, description, order_index, active,
    image_stored_name, image_mime_type, image_size_bytes,
    created_at, updated_at,
    created_by_user_id, created_by_name,
    updated_by_user_id, updated_by_name
"""


class PostgresMuralAcessosRepository(PluginBaseRepository):
    """Persistência do mural de acessos (schema mural_acessos)."""

    def list_hubs(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT
                h.id, h.title, h.subtitle, h.public_token,
                h.created_at, h.updated_at,
                COUNT(l.id)::int AS link_count
            FROM mural_acessos.hubs h
            LEFT JOIN mural_acessos.links l ON l.hub_id = h.id
            GROUP BY h.id
            ORDER BY h.title ASC, h.created_at ASC
            """
        )
        return [self._map_hub(row, link_count=int(row.get("link_count") or 0)) for row in rows]

    def get_hub(self, hub_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            SELECT {_HUB_COLUMNS}
            FROM mural_acessos.hubs
            WHERE id = %s::uuid
            """,
            (hub_id,),
        )
        return self._map_hub(row) if row else None

    def get_hub_by_token(self, public_token: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            SELECT {_HUB_COLUMNS}
            FROM mural_acessos.hubs
            WHERE public_token = %s
            """,
            (public_token,),
        )
        return self._map_hub(row) if row else None

    def create_hub(
        self,
        *,
        title: str,
        subtitle: str,
        public_token: str,
    ) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO mural_acessos.hubs (title, subtitle, public_token)
                VALUES (%s, %s, %s)
                RETURNING {_HUB_COLUMNS}
                """,
                (title, subtitle, public_token),
            )
        except PluginsRepositoryError as exc:
            self._reraise_token_conflict(exc)
            raise
        if not row:
            raise PluginsRepositoryError("Falha ao cadastrar o mural.")
        return self._map_hub(row, link_count=0)

    def update_hub(
        self,
        *,
        hub_id: str,
        title: str,
        subtitle: str,
        public_token: str,
    ) -> dict[str, Any] | None:
        try:
            row = self.execute_returning_one(
                f"""
                UPDATE mural_acessos.hubs
                SET title = %s,
                    subtitle = %s,
                    public_token = %s,
                    updated_at = NOW()
                WHERE id = %s::uuid
                RETURNING {_HUB_COLUMNS}
                """,
                (title, subtitle, public_token, hub_id),
            )
        except PluginsRepositoryError as exc:
            self._reraise_token_conflict(exc)
            raise
        return self._map_hub(row) if row else None

    def delete_hub(self, *, hub_id: str) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            DELETE FROM mural_acessos.hubs
            WHERE id = %s::uuid
            RETURNING {_HUB_COLUMNS}
            """,
            (hub_id,),
        )
        return self._map_hub(row) if row else None

    def list_links(
        self,
        *,
        hub_id: str,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT {_LINK_COLUMNS}
            FROM mural_acessos.links
            WHERE hub_id = %s::uuid
        """
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY order_index ASC, title ASC"
        return [self._map_link(row) for row in self.fetch_all(query, (hub_id,))]

    def get_link(self, link_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            SELECT {_LINK_COLUMNS}
            FROM mural_acessos.links
            WHERE id = %s::uuid
            """,
            (link_id,),
        )
        return self._map_link(row) if row else None

    def create_link(
        self,
        *,
        hub_id: str,
        title: str,
        url: str,
        description: str,
        active: bool,
        actor_id: str | None,
        actor_name: str | None,
    ) -> dict[str, Any]:
        next_order = self.fetch_one(
            """
            SELECT COALESCE(MAX(order_index), -1) + 1 AS next_order
            FROM mural_acessos.links
            WHERE hub_id = %s::uuid
            """,
            (hub_id,),
        )
        order_index = int((next_order or {}).get("next_order") or 0)
        row = self.execute_returning_one(
            f"""
            INSERT INTO mural_acessos.links (
                hub_id, title, url, description, order_index, active,
                created_by_user_id, created_by_name,
                updated_by_user_id, updated_by_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {_LINK_COLUMNS}
            """,
            (
                hub_id,
                title,
                url,
                description,
                order_index,
                active,
                actor_id,
                actor_name,
                actor_id,
                actor_name,
            ),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao cadastrar o acesso.")
        return self._map_link(row)

    def update_link(
        self,
        *,
        link_id: str,
        title: str,
        url: str,
        description: str,
        active: bool,
        actor_id: str | None,
        actor_name: str | None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            UPDATE mural_acessos.links
            SET title = %s,
                url = %s,
                description = %s,
                active = %s,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s::uuid
            RETURNING {_LINK_COLUMNS}
            """,
            (title, url, description, active, actor_id, actor_name, link_id),
        )
        return self._map_link(row) if row else None

    def delete_link(self, *, link_id: str) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            DELETE FROM mural_acessos.links
            WHERE id = %s::uuid
            RETURNING {_LINK_COLUMNS}
            """,
            (link_id,),
        )
        return self._map_link(row) if row else None

    def reorder_links(
        self, *, hub_id: str, ordered_ids: list[str]
    ) -> list[dict[str, Any]]:
        for index, link_id in enumerate(ordered_ids):
            self.execute(
                """
                UPDATE mural_acessos.links
                SET order_index = %s, updated_at = NOW()
                WHERE id = %s::uuid AND hub_id = %s::uuid
                """,
                (index, link_id, hub_id),
                auto_commit=False,
            )
        self.commit()
        return self.list_links(hub_id=hub_id)

    def set_link_image(
        self,
        *,
        link_id: str,
        stored_name: str,
        mime_type: str,
        size_bytes: int,
        actor_id: str | None,
        actor_name: str | None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            UPDATE mural_acessos.links
            SET image_stored_name = %s,
                image_mime_type = %s,
                image_size_bytes = %s,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s::uuid
            RETURNING {_LINK_COLUMNS}
            """,
            (stored_name, mime_type, size_bytes, actor_id, actor_name, link_id),
        )
        return self._map_link(row) if row else None

    def clear_link_image(
        self,
        *,
        link_id: str,
        actor_id: str | None,
        actor_name: str | None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            UPDATE mural_acessos.links
            SET image_stored_name = NULL,
                image_mime_type = NULL,
                image_size_bytes = NULL,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s::uuid
            RETURNING {_LINK_COLUMNS}
            """,
            (actor_id, actor_name, link_id),
        )
        return self._map_link(row) if row else None

    @staticmethod
    def _reraise_token_conflict(exc: PluginsRepositoryError) -> None:
        cause = exc.__cause__
        if isinstance(cause, UniqueViolation):
            raise MuralAcessosValidationError(
                "Já existe um mural com este identificador público."
            ) from exc

    @staticmethod
    def _map_hub(
        row: dict[str, Any], *, link_count: int | None = None
    ) -> dict[str, Any]:
        payload = {
            "id": str(row["id"]),
            "title": row["title"],
            "subtitle": row.get("subtitle") or "",
            "publicToken": row["public_token"],
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }
        if link_count is not None:
            payload["linkCount"] = link_count
        return payload

    @staticmethod
    def _map_link(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "hubId": str(row["hub_id"]),
            "title": row["title"],
            "url": row["url"],
            "description": row.get("description") or "",
            "orderIndex": int(row.get("order_index") or 0),
            "active": bool(row.get("active")),
            "hasImage": bool(row.get("image_stored_name")),
            "imageStoredName": row.get("image_stored_name"),
            "imageMimeType": row.get("image_mime_type"),
            "imageSizeBytes": row.get("image_size_bytes"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
            "createdByName": row.get("created_by_name"),
            "updatedByName": row.get("updated_by_name"),
        }
