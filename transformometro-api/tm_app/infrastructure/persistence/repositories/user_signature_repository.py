from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class UserSignatureRepository(PluginBaseRepository):
    def get_by_user(self, user_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """SELECT user_id, display_name, signature_path, updated_at
               FROM transformometro.tm_user_signature_profiles WHERE user_id = %s::uuid""",
            (user_id,),
        )

    def upsert_profile(self, *, user_id: str, display_name: str) -> dict[str, Any]:
        row = self.execute_returning_one(
            """INSERT INTO transformometro.tm_user_signature_profiles (user_id, display_name, updated_at)
               VALUES (%s::uuid, %s, NOW())
               ON CONFLICT (user_id) DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = NOW()
               RETURNING user_id, display_name, signature_path, updated_at""",
            (user_id, display_name),
        )
        if row is None:
            raise RuntimeError("Falha ao salvar perfil de assinatura.")
        return row

    def update_signature_path(
        self, *, user_id: str, signature_path: str, display_name: str | None = None
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """INSERT INTO transformometro.tm_user_signature_profiles
                 (user_id, display_name, signature_path, updated_at)
               VALUES (%s::uuid, %s, %s, NOW())
               ON CONFLICT (user_id) DO UPDATE SET
                 signature_path = EXCLUDED.signature_path,
                 display_name = COALESCE(NULLIF(EXCLUDED.display_name, ''),
                   transformometro.tm_user_signature_profiles.display_name),
                 updated_at = NOW()
               RETURNING user_id, display_name, signature_path, updated_at""",
            (user_id, display_name or "", signature_path),
        )
        if row is None:
            raise RuntimeError("Falha ao salvar assinatura.")
        return row
