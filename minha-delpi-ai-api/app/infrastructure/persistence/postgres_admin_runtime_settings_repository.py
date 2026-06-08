from datetime import datetime, timezone

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.extensions.db import db
from app.infrastructure.db.models.admin_runtime_settings_model import (
    AiAdminRuntimeSettingsModel,
)

LLM_COST_TABLE_KEY = "llm_cost_table"
CHAT_INTELLIGENCE_SETTINGS_KEY = "chat_intelligence_settings"


class PostgresAdminRuntimeSettingsRepository(AdminRuntimeSettingsRepositoryPort):
    def get_json(self, key: str) -> object | None:
        row = AiAdminRuntimeSettingsModel.query.filter_by(key=key).first()

        if not row:
            return None

        return row.value

    def set_json(self, key: str, value: object) -> None:
        row = AiAdminRuntimeSettingsModel.query.filter_by(key=key).first()
        now = datetime.now(timezone.utc)

        if row:
            row.value = value
            row.updated_at = now
        else:
            db.session.add(
                AiAdminRuntimeSettingsModel(
                    key=key,
                    value=value,
                    updated_at=now,
                )
            )

        db.session.flush()

    def get_llm_cost_table(self) -> list[dict] | None:
        value = self.get_json(LLM_COST_TABLE_KEY)

        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]

        return None

    def save_llm_cost_table(self, entries: list[dict]) -> None:
        self.set_json(LLM_COST_TABLE_KEY, entries)

    def get_chat_intelligence_settings(self) -> dict | None:
        value = self.get_json(CHAT_INTELLIGENCE_SETTINGS_KEY)

        if isinstance(value, dict):
            return dict(value)

        return None

    def save_chat_intelligence_settings(self, payload: dict) -> None:
        self.set_json(CHAT_INTELLIGENCE_SETTINGS_KEY, payload)
