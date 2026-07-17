from __future__ import annotations

from typing import Any
from uuid import UUID

from cipa_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    get_connection,
)


def _uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


class UserSignatureRepository:
    def get_by_user(self, user_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, display_name, signature_path, updated_at
                    FROM cipa.user_signature_profiles
                    WHERE user_id = %s
                    """,
                    (_uuid(user_id),),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def upsert_profile(self, *, user_id: str, display_name: str) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cipa.user_signature_profiles (user_id, display_name, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE
                      SET display_name = EXCLUDED.display_name,
                          updated_at = NOW()
                    RETURNING user_id, display_name, signature_path, updated_at
                    """,
                    (_uuid(user_id), display_name),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row)

    def update_signature_path(
        self,
        *,
        user_id: str,
        signature_path: str,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if display_name is not None:
                    cur.execute(
                        """
                        INSERT INTO cipa.user_signature_profiles (
                            user_id, display_name, signature_path, updated_at
                        )
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (user_id) DO UPDATE
                          SET signature_path = EXCLUDED.signature_path,
                              display_name = COALESCE(
                                NULLIF(EXCLUDED.display_name, ''),
                                cipa.user_signature_profiles.display_name
                              ),
                              updated_at = NOW()
                        RETURNING user_id, display_name, signature_path, updated_at
                        """,
                        (_uuid(user_id), display_name or "", signature_path),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO cipa.user_signature_profiles (
                            user_id, display_name, signature_path, updated_at
                        )
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (user_id) DO UPDATE
                          SET signature_path = EXCLUDED.signature_path,
                              updated_at = NOW()
                        RETURNING user_id, display_name, signature_path, updated_at
                        """,
                        (_uuid(user_id), "", signature_path),
                    )
                row = cur.fetchone()
                conn.commit()
                return dict(row)
