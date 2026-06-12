from __future__ import annotations

from typing import Any

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.infrastructure.config.chat_admin_settings_bundles import (
    AdminSettingsBundleSpec,
    build_defaults_payload,
    resolve_bundle_payload,
)


class ChatAdminSettingsBundleService:
    """Bundle de configuração admin: admin prevalece; .env só como default inicial."""

    def __init__(
        self,
        spec: AdminSettingsBundleSpec,
        settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
    ):
        self.spec = spec
        self.settings_repository = settings_repository

    def _load_stored(self) -> dict[str, Any] | None:
        if self.settings_repository is None:
            return None

        value = self.settings_repository.get_json(self.spec.storage_key)

        if isinstance(value, dict):
            return dict(value)

        return None

    def resolve(self) -> dict[str, Any]:
        return resolve_bundle_payload(spec=self.spec, stored=self._load_stored())

    def ensure_defaults_seeded(self) -> dict[str, Any]:
        if self._load_stored():
            return self.to_dict()

        payload = build_defaults_payload(self.spec)

        if self.settings_repository is not None:
            self.settings_repository.set_json(self.spec.storage_key, payload)

        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        resolved = self.resolve()
        stored = self._load_stored()

        return {
            **resolved,
            "source": "admin" if stored else "defaults",
            "defaults": build_defaults_payload(self.spec),
        }

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.resolve()
        merged = dict(current)

        for field in self.spec.fields:
            if field.json_key in payload:
                merged[field.json_key] = payload[field.json_key]

        normalized = resolve_bundle_payload(spec=self.spec, stored=merged)

        if self.settings_repository is not None:
            self.settings_repository.set_json(self.spec.storage_key, normalized)

        return self.to_dict()
