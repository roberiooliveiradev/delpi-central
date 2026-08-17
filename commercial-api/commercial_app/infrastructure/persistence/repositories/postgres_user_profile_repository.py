from __future__ import annotations

from typing import Any

from commercial_app.domain.entities.user_profile import CommercialUserProfile
from commercial_app.domain.ports.user_profile_repository_port import UserProfileRepositoryPort
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = """
    user_id, job_title, phone_e164, mobile_e164, whatsapp_e164,
    photo_storage_key, photo_file_name, photo_content_type, photo_byte_size,
    created_at, updated_at
"""


def _row(row: dict[str, Any] | None) -> CommercialUserProfile | None:
    if not row:
        return None
    return CommercialUserProfile(
        user_id=str(row["user_id"]),
        job_title=row.get("job_title"),
        phone_e164=row.get("phone_e164"),
        mobile_e164=row.get("mobile_e164"),
        whatsapp_e164=row.get("whatsapp_e164"),
        photo_storage_key=row.get("photo_storage_key"),
        photo_file_name=row.get("photo_file_name"),
        photo_content_type=row.get("photo_content_type"),
        photo_byte_size=row.get("photo_byte_size"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresUserProfileRepository(PluginBaseRepository, UserProfileRepositoryPort):
    def get(self, user_id: str) -> CommercialUserProfile | None:
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.commercial_user_profiles
             WHERE user_id = %s
            """,
            (user_id.strip(),),
        )
        return _row(row)

    def upsert_profile_fields(
        self,
        *,
        user_id: str,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> CommercialUserProfile:
        title = (job_title or "").strip() or None
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.commercial_user_profiles (
                user_id, job_title, phone_e164, mobile_e164, whatsapp_e164
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
               SET job_title = EXCLUDED.job_title,
                   phone_e164 = EXCLUDED.phone_e164,
                   mobile_e164 = EXCLUDED.mobile_e164,
                   whatsapp_e164 = EXCLUDED.whatsapp_e164,
                   updated_at = NOW()
         RETURNING {_COLUMNS}
            """,
            (
                user_id.strip(),
                title,
                phone_e164,
                mobile_e164,
                whatsapp_e164,
            ),
        )
        profile = _row(row)
        if profile is None:
            raise RuntimeError("Falha ao salvar perfil do usuário.")
        return profile

    def upsert_photo(
        self,
        *,
        user_id: str,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> CommercialUserProfile:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.commercial_user_profiles (
                user_id, photo_storage_key, photo_file_name,
                photo_content_type, photo_byte_size
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
               SET photo_storage_key = EXCLUDED.photo_storage_key,
                   photo_file_name = EXCLUDED.photo_file_name,
                   photo_content_type = EXCLUDED.photo_content_type,
                   photo_byte_size = EXCLUDED.photo_byte_size,
                   updated_at = NOW()
         RETURNING {_COLUMNS}
            """,
            (user_id.strip(), storage_key, file_name, content_type, byte_size),
        )
        profile = _row(row)
        if profile is None:
            raise RuntimeError("Falha ao salvar foto do usuário.")
        return profile

    def clear_photo(self, *, user_id: str) -> CommercialUserProfile | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.commercial_user_profiles
               SET photo_storage_key = NULL,
                   photo_file_name = NULL,
                   photo_content_type = NULL,
                   photo_byte_size = NULL,
                   updated_at = NOW()
             WHERE user_id = %s
         RETURNING {_COLUMNS}
            """,
            (user_id.strip(),),
        )
        return _row(row)
