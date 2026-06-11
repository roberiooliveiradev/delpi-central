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

    @classmethod
    def chat_web_search_direct_response_enabled(cls) -> bool:
        return cls._require_config().chat_web_search_direct_response_enabled()

    @classmethod
    def chat_web_search_enabled(cls) -> bool:
        return cls._require_config().chat_web_search_enabled()

    @classmethod
    def chat_web_search_max_results(cls) -> int:
        return cls._require_config().chat_web_search_max_results()

    @classmethod
    def chat_web_search_timeout_seconds(cls) -> float:
        return cls._require_config().chat_web_search_timeout_seconds()

    @classmethod
    def chat_web_search_auto_augment_enabled(cls) -> bool:
        return cls._require_config().chat_web_search_auto_augment_enabled()

    @classmethod
    def chat_pagination_auto_fetch_enabled(cls) -> bool:
        return cls._require_config().chat_pagination_auto_fetch_enabled()

    @classmethod
    def chat_pagination_max_pages_per_turn(cls) -> int:
        return cls._require_config().chat_pagination_max_pages_per_turn()

    @classmethod
    def chat_operational_fast_path_enabled(cls) -> bool:
        return cls._require_config().chat_operational_fast_path_enabled()

    @classmethod
    def chat_default_sql_dialect(cls) -> str:
        return cls._require_config().chat_default_sql_dialect()

    @classmethod
    def llm_provider(cls) -> str:
        return cls._require_config().llm_provider()

    @classmethod
    def vllm_model(cls) -> str:
        return cls._require_config().vllm_model()

    @classmethod
    def ollama_model(cls) -> str:
        return cls._require_config().ollama_model()

    @classmethod
    def llm_max_tokens(cls) -> int:
        return cls._require_config().llm_max_tokens()

    @classmethod
    def ollama_num_ctx(cls) -> int:
        return cls._require_config().ollama_num_ctx()

    @classmethod
    def llm_temperature(cls) -> float:
        return cls._require_config().llm_temperature()

    @classmethod
    def chat_agentic_catalog_max_actions(cls) -> int:
        return cls._require_config().chat_agentic_catalog_max_actions()

    @classmethod
    def chat_agentic_schema_max_parameters(cls) -> int:
        return cls._require_config().chat_agentic_schema_max_parameters()

    @classmethod
    def chat_drawing_pdf_max_pages(cls) -> int:
        return cls._require_config().chat_drawing_pdf_max_pages()

    @classmethod
    def chat_drawing_pdf_min_legible_chars(cls) -> int:
        return cls._require_config().chat_drawing_pdf_min_legible_chars()

    @classmethod
    def chat_message_max_chars(cls) -> int:
        return cls._require_config().chat_message_max_chars()

    @classmethod
    def chat_input_security_enabled(cls) -> bool:
        return cls._require_config().chat_input_security_enabled()

    @classmethod
    def chat_input_security_mode(cls) -> str:
        return cls._require_config().chat_input_security_mode()

    @classmethod
    def chat_input_security_block_threshold(cls) -> float:
        return cls._require_config().chat_input_security_block_threshold()

    @classmethod
    def chat_input_security_flag_threshold(cls) -> float:
        return cls._require_config().chat_input_security_flag_threshold()

    @classmethod
    def rate_limit_enabled(cls) -> bool:
        return cls._require_config().rate_limit_enabled()

    @classmethod
    def rate_limit_window_seconds(cls) -> int:
        return cls._require_config().rate_limit_window_seconds()

    @classmethod
    def rate_limit_chat_messages_per_window(cls) -> int:
        return cls._require_config().rate_limit_chat_messages_per_window()

    @classmethod
    def rate_limit_tool_calls_per_window(cls) -> int:
        return cls._require_config().rate_limit_tool_calls_per_window()

    @classmethod
    def rate_limit_knowledge_writes_per_window(cls) -> int:
        return cls._require_config().rate_limit_knowledge_writes_per_window()

    @classmethod
    def rate_limit_admin_actions_per_window(cls) -> int:
        return cls._require_config().rate_limit_admin_actions_per_window()

    @classmethod
    def chat_presentation_column_label_discovery_enabled(cls) -> bool:
        return cls._require_config().chat_presentation_column_label_discovery_enabled()

    @classmethod
    def chat_presentation_column_label_web_search_enabled(cls) -> bool:
        return cls._require_config().chat_presentation_column_label_web_search_enabled()

    @classmethod
    def chat_presentation_column_label_max_keys(cls) -> int:
        return cls._require_config().chat_presentation_column_label_max_keys()

    @classmethod
    def chat_presentation_column_label_web_max_queries(cls) -> int:
        return cls._require_config().chat_presentation_column_label_web_max_queries()

    @classmethod
    def chat_presentation_column_label_cache_size(cls) -> int:
        return cls._require_config().chat_presentation_column_label_cache_size()
