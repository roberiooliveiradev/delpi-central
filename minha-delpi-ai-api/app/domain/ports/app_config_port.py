from __future__ import annotations

from abc import ABC, abstractmethod


class AppConfigPort(ABC):
    """Flags e limites usados pelo domain sem importar Settings."""

    @abstractmethod
    def chat_external_action_direct_response_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_direct_response_stream_chunk_chars(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_direct_response_stream_delay_ms(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_default_sql_authoring_skill_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_document_vision_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_document_vision_auto_with_drawing(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_response_modes_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_typing_correction_fuzzy_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_text_correction_spell_check_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_languagetool_language(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def learning_pipeline_flag(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_direct_response_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_max_results(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_timeout_seconds(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_auto_augment_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_web_search_retry_en_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_pagination_auto_fetch_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_pagination_max_pages_per_turn(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_operational_fast_path_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_default_sql_dialect(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def llm_provider(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def vllm_model(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def ollama_model(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def llm_max_tokens(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def ollama_num_ctx(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def llm_temperature(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def chat_agentic_catalog_max_actions(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_agentic_schema_max_parameters(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_drawing_pdf_max_pages(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_drawing_pdf_min_legible_chars(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_message_max_chars(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_input_security_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_input_security_mode(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def chat_input_security_block_threshold(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def chat_input_security_flag_threshold(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_window_seconds(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_chat_messages_per_window(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_tool_calls_per_window(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_knowledge_writes_per_window(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def rate_limit_admin_actions_per_window(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_presentation_column_label_discovery_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_presentation_column_label_web_search_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat_presentation_column_label_max_keys(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_presentation_column_label_web_max_queries(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_presentation_column_label_cache_size(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_attachment_index_pdf_page_limit(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_document_vision_dpi(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def chat_attachment_storage_path(self) -> str:
        raise NotImplementedError
