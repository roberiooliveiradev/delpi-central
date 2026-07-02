from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = (
    "id, user_id, display_name, role_title, signature_filename, signature_mime, "
    "signature_updated_at, created_at, updated_at"
)


class PostgresQualityLabelsInspectorRepository(PluginBaseRepository):
    """Perfil e assinatura do inspetor (por usuário do Core API)."""

    def get_by_user(self, user_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_COLUMNS} FROM quality_labels.inspectors WHERE user_id = %s",
            (user_id,),
        )

    def upsert_profile(
        self,
        *,
        user_id: str,
        display_name: str,
        role_title: str | None,
    ) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            INSERT INTO quality_labels.inspectors (user_id, display_name, role_title)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
               SET display_name = EXCLUDED.display_name,
                   role_title = EXCLUDED.role_title,
                   updated_at = NOW()
            RETURNING {_COLUMNS}
            """,
            (user_id, display_name, role_title),
        )

    def set_signature(
        self,
        *,
        user_id: str,
        display_name: str,
        signature_filename: str,
        signature_mime: str,
    ) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            INSERT INTO quality_labels.inspectors (
                user_id, display_name, signature_filename, signature_mime,
                signature_updated_at
            ) VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE
               SET signature_filename = EXCLUDED.signature_filename,
                   signature_mime = EXCLUDED.signature_mime,
                   signature_updated_at = NOW(),
                   display_name = COALESCE(NULLIF(quality_labels.inspectors.display_name, ''), EXCLUDED.display_name),
                   updated_at = NOW()
            RETURNING {_COLUMNS}
            """,
            (user_id, display_name, signature_filename, signature_mime),
        )

    @staticmethod
    def _iso(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @classmethod
    def to_payload(cls, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        return {
            "id": str(row.get("id")),
            "userId": row.get("user_id"),
            "displayName": row.get("display_name"),
            "roleTitle": row.get("role_title"),
            "hasSignature": bool(row.get("signature_filename")),
            "signatureUpdatedAt": cls._iso(row.get("signature_updated_at")),
            "updatedAt": cls._iso(row.get("updated_at")),
        }
