"""Acesso a flags de ambiente no domain via AppConfigPort."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.app_config_port import AppConfigPort


class ChatDomainConfigService:
    _config: ClassVar[AppConfigPort | None] = None

    @classmethod
    def configure(cls, config: AppConfigPort) -> None:
        cls._config = config

    @classmethod
    def _require_config(cls) -> AppConfigPort:
        if cls._config is None:
            raise RuntimeError(
                "AppConfigPort não configurado — chame configure_domain_infrastructure_ports()"
            )

        return cls._config

    @classmethod
    def chat_default_sql_authoring_skill_enabled(cls) -> bool:
        return cls._require_config().chat_default_sql_authoring_skill_enabled()

    @classmethod
    def chat_document_vision_enabled(cls) -> bool:
        return cls._require_config().chat_document_vision_enabled()

    @classmethod
    def chat_document_vision_auto_with_drawing(cls) -> bool:
        return cls._require_config().chat_document_vision_auto_with_drawing()
