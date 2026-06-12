from __future__ import annotations

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.infrastructure.config.chat_admin_settings_bundles import (
    AdminSettingsBundleSpec,
    CHAT_LEARNING_PIPELINE_BUNDLE,
    CHAT_RESPONSE_MODE_BUNDLE,
    CHAT_VISION_BUNDLE,
    resolve_bundle_payload,
    build_defaults_payload,
)


def read_admin_settings_bundle(
    spec: AdminSettingsBundleSpec,
    settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
) -> dict:
    stored = None

    if settings_repository is not None:
        value = settings_repository.get_json(spec.storage_key)
        if isinstance(value, dict):
            stored = dict(value)

    return resolve_bundle_payload(spec=spec, stored=stored)


def read_response_mode_settings(
    settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
) -> dict:
    return read_admin_settings_bundle(CHAT_RESPONSE_MODE_BUNDLE, settings_repository)


def read_vision_settings(
    settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
) -> dict:
    return read_admin_settings_bundle(CHAT_VISION_BUNDLE, settings_repository)


def read_learning_pipeline_settings(
    settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
) -> dict:
    return read_admin_settings_bundle(CHAT_LEARNING_PIPELINE_BUNDLE, settings_repository)


def bundle_defaults(spec: AdminSettingsBundleSpec) -> dict:
    return build_defaults_payload(spec)
