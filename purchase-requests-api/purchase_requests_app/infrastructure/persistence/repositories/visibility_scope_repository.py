from __future__ import annotations

from typing import Any

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class VisibilityScopeRepository:
    def list_active_cost_centers_for_user(self, user_id: str) -> list[dict[str, Any]]:
        sql = """
        SELECT DISTINCT cc.branch, cc.cost_center_code
        FROM purchase_requests.visibility_scope_users su
        JOIN purchase_requests.visibility_scopes vs ON vs.id = su.scope_id
        JOIN purchase_requests.visibility_scope_cost_centers cc ON cc.scope_id = vs.id
        WHERE vs.active = TRUE
          AND su.user_id = %s
        ORDER BY cc.branch, cc.cost_center_code
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def list_scopes(self) -> list[dict[str, Any]]:
        sql = """
        SELECT id, name, description, active, created_at, updated_at
        FROM purchase_requests.visibility_scopes
        ORDER BY name ASC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [self._hydrate_scope(dict(row)) for row in rows]

    def get_scope(self, scope_id: str) -> dict[str, Any] | None:
        sql = """
        SELECT id, name, description, active, created_at, updated_at
        FROM purchase_requests.visibility_scopes
        WHERE id = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (scope_id,))
                row = cur.fetchone()
        if not row:
            return None
        return self._hydrate_scope(dict(row), include_children=True)

    def create_scope(
        self,
        *,
        name: str,
        description: str | None,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        sql = """
        INSERT INTO purchase_requests.visibility_scopes
            (name, description, created_by_user_id, updated_by_user_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, description, active, created_at, updated_at
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name.strip(), description, actor_user_id, actor_user_id))
                row = cur.fetchone()
            conn.commit()
        return self._hydrate_scope(dict(row))

    def update_scope(
        self,
        scope_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        actor_user_id: str | None = None,
    ) -> dict[str, Any] | None:
        fields: list[str] = []
        params: list[Any] = []
        if name is not None:
            fields.append("name = %s")
            params.append(name.strip())
        if description is not None:
            fields.append("description = %s")
            params.append(description)
        if active is not None:
            fields.append("active = %s")
            params.append(active)
        if not fields:
            return self.get_scope(scope_id)
        fields.append("updated_by_user_id = %s")
        params.append(actor_user_id)
        fields.append("updated_at = NOW()")
        params.append(scope_id)
        sql = f"""
        UPDATE purchase_requests.visibility_scopes
        SET {", ".join(fields)}
        WHERE id = %s
        RETURNING id, name, description, active, created_at, updated_at
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                row = cur.fetchone()
            conn.commit()
        if not row:
            return None
        return self._hydrate_scope(dict(row), include_children=True)

    def replace_users(self, scope_id: str, user_ids: list[str]) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM purchase_requests.visibility_scope_users WHERE scope_id = %s",
                    (scope_id,),
                )
                for user_id in user_ids:
                    cur.execute(
                        """
                        INSERT INTO purchase_requests.visibility_scope_users (scope_id, user_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (scope_id, user_id),
                    )
            conn.commit()
        return self.get_scope(scope_id)

    def replace_cost_centers(
        self,
        scope_id: str,
        cost_centers: list[dict[str, str]],
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM purchase_requests.visibility_scope_cost_centers WHERE scope_id = %s",
                    (scope_id,),
                )
                for item in cost_centers:
                    cur.execute(
                        """
                        INSERT INTO purchase_requests.visibility_scope_cost_centers
                            (scope_id, branch, cost_center_code)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (scope_id, item["branch"].strip(), item["cost_center_code"].strip()),
                    )
            conn.commit()
        return self.get_scope(scope_id)

    def _hydrate_scope(self, row: dict[str, Any], *, include_children: bool = False) -> dict[str, Any]:
        scope_id = str(row["id"])
        payload = {
            "id": scope_id,
            "name": row["name"],
            "description": row.get("description"),
            "active": bool(row["active"]),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "users": [],
            "cost_centers": [],
        }
        if not include_children:
            return payload
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id FROM purchase_requests.visibility_scope_users
                    WHERE scope_id = %s ORDER BY user_id
                    """,
                    (scope_id,),
                )
                payload["users"] = [r["user_id"] for r in cur.fetchall()]
                cur.execute(
                    """
                    SELECT branch, cost_center_code
                    FROM purchase_requests.visibility_scope_cost_centers
                    WHERE scope_id = %s
                    ORDER BY branch, cost_center_code
                    """,
                    (scope_id,),
                )
                payload["cost_centers"] = [dict(r) for r in cur.fetchall()]
        return payload
