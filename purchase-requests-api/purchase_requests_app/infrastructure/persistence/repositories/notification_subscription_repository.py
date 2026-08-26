from __future__ import annotations

from typing import Any

from purchase_requests_app.domain.services.notification_event_catalog import (
    is_valid_notification_event_key,
)
from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class NotificationSubscriptionRepository:
    def list_all(self) -> list[dict[str, Any]]:
        sql = """
        SELECT user_id, event_key, enabled, created_at, updated_at
        FROM purchase_requests.user_notification_subscriptions
        ORDER BY user_id, event_key
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        sql = """
        SELECT user_id, event_key, enabled, created_at, updated_at
        FROM purchase_requests.user_notification_subscriptions
        WHERE user_id = %s
        ORDER BY event_key
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def replace_for_user(
        self,
        user_id: str,
        subscriptions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        cleaned: list[tuple[str, bool]] = []
        seen: set[str] = set()
        for item in subscriptions:
            event_key = str(item.get("event_key") or "").strip()
            if not event_key or event_key in seen:
                continue
            if not is_valid_notification_event_key(event_key):
                raise ValueError(f"Evento de notificação inválido: {event_key}")
            seen.add(event_key)
            cleaned.append((event_key, bool(item.get("enabled"))))

        delete_sql = """
        DELETE FROM purchase_requests.user_notification_subscriptions
        WHERE user_id = %s
        """
        insert_sql = """
        INSERT INTO purchase_requests.user_notification_subscriptions
            (user_id, event_key, enabled)
        VALUES (%s, %s, %s)
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(delete_sql, (user_id,))
                for event_key, enabled in cleaned:
                    if enabled:
                        cur.execute(insert_sql, (user_id, event_key, True))
            conn.commit()
        return self.list_for_user(user_id)
