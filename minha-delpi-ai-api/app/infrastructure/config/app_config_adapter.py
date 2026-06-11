from __future__ import annotations

from app.domain.ports.app_config_port import AppConfigPort
from app.infrastructure.config.settings import Settings


class InfrastructureAppConfigAdapter(AppConfigPort):
    def chat_external_action_direct_response_enabled(self) -> bool:
        return bool(Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED)

    def chat_direct_response_stream_chunk_chars(self) -> int:
        return int(Settings.CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS)

    def chat_direct_response_stream_delay_ms(self) -> int:
        return int(Settings.CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS)

    def chat_default_sql_authoring_skill_enabled(self) -> bool:
        return bool(Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL)

    def chat_document_vision_enabled(self) -> bool:
        return bool(Settings.CHAT_DOCUMENT_VISION_ENABLED)

    def chat_document_vision_auto_with_drawing(self) -> bool:
        return bool(Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING)

    def chat_web_search_direct_response_enabled(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED)

    def chat_web_search_enabled(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_ENABLED)

    def chat_web_search_max_results(self) -> int:
        return int(Settings.CHAT_WEB_SEARCH_MAX_RESULTS)

    def chat_web_search_timeout_seconds(self) -> float:
        return float(Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS)

    def chat_web_search_auto_augment_enabled(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_AUTO_AUGMENT_ENABLED)

    def chat_pagination_auto_fetch_enabled(self) -> bool:
        return bool(Settings.CHAT_PAGINATION_AUTO_FETCH_ENABLED)

    def chat_pagination_max_pages_per_turn(self) -> int:
        return int(Settings.CHAT_PAGINATION_MAX_PAGES_PER_TURN)

    def chat_operational_fast_path_enabled(self) -> bool:
        return bool(Settings.CHAT_OPERATIONAL_FAST_PATH_ENABLED)

    def chat_default_sql_dialect(self) -> str:
        return str(Settings.CHAT_DEFAULT_SQL_DIALECT or "sqlserver").strip().lower()

    def llm_provider(self) -> str:
        return str(Settings.LLM_PROVIDER)

    def vllm_model(self) -> str:
        return str(Settings.VLLM_MODEL)

    def ollama_model(self) -> str:
        from app.domain.services.chat_fine_tuning_deploy_resolver_service import (
            ChatFineTuningDeployResolverService,
        )

        return ChatFineTuningDeployResolverService.resolve(str(Settings.OLLAMA_MODEL))

    def llm_max_tokens(self) -> int:
        return int(Settings.LLM_MAX_TOKENS)

    def ollama_num_ctx(self) -> int:
        return int(Settings.OLLAMA_NUM_CTX)

    def llm_temperature(self) -> float:
        return float(Settings.LLM_TEMPERATURE)

    def chat_agentic_catalog_max_actions(self) -> int:
        return int(Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS)

    def chat_agentic_schema_max_parameters(self) -> int:
        return int(Settings.CHAT_AGENTIC_SCHEMA_MAX_PARAMETERS)

    def chat_drawing_pdf_max_pages(self) -> int:
        return int(Settings.CHAT_DRAWING_PDF_MAX_PAGES)

    def chat_drawing_pdf_min_legible_chars(self) -> int:
        return int(Settings.CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS)

    def chat_message_max_chars(self) -> int:
        return int(Settings.CHAT_MESSAGE_MAX_CHARS)

    def chat_input_security_enabled(self) -> bool:
        return bool(Settings.CHAT_INPUT_SECURITY_ENABLED)

    def chat_input_security_mode(self) -> str:
        return str(Settings.CHAT_INPUT_SECURITY_MODE)

    def chat_input_security_block_threshold(self) -> float:
        return float(Settings.CHAT_INPUT_SECURITY_BLOCK_THRESHOLD)

    def chat_input_security_flag_threshold(self) -> float:
        return float(Settings.CHAT_INPUT_SECURITY_FLAG_THRESHOLD)

    def rate_limit_enabled(self) -> bool:
        return bool(Settings.RATE_LIMIT_ENABLED)

    def rate_limit_window_seconds(self) -> int:
        return int(Settings.RATE_LIMIT_WINDOW_SECONDS)

    def rate_limit_chat_messages_per_window(self) -> int:
        return int(Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)

    def rate_limit_tool_calls_per_window(self) -> int:
        return int(Settings.RATE_LIMIT_TOOL_CALLS_PER_WINDOW)

    def rate_limit_knowledge_writes_per_window(self) -> int:
        return int(Settings.RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW)

    def rate_limit_admin_actions_per_window(self) -> int:
        return int(Settings.RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW)

    def chat_presentation_column_label_discovery_enabled(self) -> bool:
        return bool(Settings.CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED)

    def chat_presentation_column_label_web_search_enabled(self) -> bool:
        return bool(Settings.CHAT_PRESENTATION_COLUMN_LABEL_WEB_SEARCH_ENABLED)

    def chat_presentation_column_label_max_keys(self) -> int:
        return int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_MAX_KEYS)

    def chat_presentation_column_label_web_max_queries(self) -> int:
        return int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_WEB_MAX_QUERIES)

    def chat_presentation_column_label_cache_size(self) -> int:
        return int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_CACHE_SIZE)
