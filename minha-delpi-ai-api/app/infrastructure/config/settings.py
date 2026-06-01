import os

from app.infrastructure.config.llm_latency_profile import (
    resolve_llm_max_tokens,
    resolve_ollama_num_ctx,
)


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "minha-delpi-ai-api")
    ENV = os.getenv("FLASK_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DATABASE_URL = os.getenv("DATABASE_URL", "")

    KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "")
    KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "")
    JWT_ALGORITHMS = os.getenv("JWT_ALGORITHMS", "RS256")

    CORE_API_BASE_URL = os.getenv("CORE_API_BASE_URL", "http://core-api:8000")
    CORE_API_TIMEOUT_SECONDS = float(os.getenv("CORE_API_TIMEOUT_SECONDS", "5"))

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))
    LLM_MAX_TOKENS = resolve_llm_max_tokens()
    LLM_PROMPT_TOKEN_COST_PER_1K = float(
        os.getenv("LLM_PROMPT_TOKEN_COST_PER_1K", "0")
    )
    LLM_COMPLETION_TOKEN_COST_PER_1K = float(
        os.getenv("LLM_COMPLETION_TOKEN_COST_PER_1K", "0")
    )
    RAG_ASSERTIVENESS_MIN_SCORE = float(
        os.getenv("RAG_ASSERTIVENESS_MIN_SCORE", "0.35")
    )
    RAG_CONTEXT_MIN_SCORE = float(
        os.getenv(
            "RAG_CONTEXT_MIN_SCORE",
            os.getenv("RAG_ASSERTIVENESS_MIN_SCORE", "0.35"),
        )
    )
    # Perguntas meta («quem te criou», «o que você é») costumam ter score semântico mais baixo.
    RAG_IDENTITY_QUESTION_MIN_SCORE = float(
        os.getenv("RAG_IDENTITY_QUESTION_MIN_SCORE", "0.22"),
    )

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
    OLLAMA_NUM_CTX = resolve_ollama_num_ctx()
    OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "0"))

    VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
    VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    VLLM_API_KEY = os.getenv("VLLM_API_KEY", "minha-delpi-local-vllm")
    VLLM_TIMEOUT_SECONDS = float(os.getenv("VLLM_TIMEOUT_SECONDS", "300"))

    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "120"))

    CHAT_SESSION_TITLE_LLM_ENABLED = (
        os.getenv("CHAT_SESSION_TITLE_LLM_ENABLED", "true").lower() == "true"
    )
    CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "12"))
    CHAT_MESSAGE_MAX_CHARS = int(os.getenv("CHAT_MESSAGE_MAX_CHARS", "8000"))
    CHAT_INPUT_SECURITY_ENABLED = (
        os.getenv("CHAT_INPUT_SECURITY_ENABLED", "true").lower() == "true"
    )
    CHAT_INPUT_SECURITY_MODE = os.getenv("CHAT_INPUT_SECURITY_MODE", "enforce").lower().strip()
    CHAT_INPUT_SECURITY_BLOCK_THRESHOLD = float(
        os.getenv("CHAT_INPUT_SECURITY_BLOCK_THRESHOLD", "0.7")
    )
    CHAT_INPUT_SECURITY_FLAG_THRESHOLD = float(
        os.getenv("CHAT_INPUT_SECURITY_FLAG_THRESHOLD", "0.35")
    )
    MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "8"))
    MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))

    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW = int(
        os.getenv("RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW", "20")
    )
    RATE_LIMIT_TOOL_CALLS_PER_WINDOW = int(
        os.getenv("RATE_LIMIT_TOOL_CALLS_PER_WINDOW", "30")
    )
    RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW = int(
        os.getenv("RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW", "10")
    )
    RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW = int(
        os.getenv("RATE_LIMIT_ADMIN_ACTIONS_PER_WINDOW", "20")
    )

    KNOWLEDGE_TITLE_MAX_CHARS = int(os.getenv("KNOWLEDGE_TITLE_MAX_CHARS", "200"))
    KNOWLEDGE_SOURCE_REF_MAX_CHARS = int(
        os.getenv("KNOWLEDGE_SOURCE_REF_MAX_CHARS", "500")
    )
    KNOWLEDGE_DOCUMENT_MAX_CHARS = int(
        os.getenv("KNOWLEDGE_DOCUMENT_MAX_CHARS", "2000000")
    )
    KNOWLEDGE_CHUNK_SIZE = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "1400"))
    KNOWLEDGE_CHUNK_MIN_SIZE = int(os.getenv("KNOWLEDGE_CHUNK_MIN_SIZE", "800"))
    KNOWLEDGE_CHUNK_OVERLAP = int(os.getenv("KNOWLEDGE_CHUNK_OVERLAP", "200"))
    KNOWLEDGE_PIPELINE_ENABLED = (
        os.getenv("KNOWLEDGE_PIPELINE_ENABLED", "true").lower() == "true"
    )
    KNOWLEDGE_SEMANTIC_DEDUP_ENABLED = (
        os.getenv("KNOWLEDGE_SEMANTIC_DEDUP_ENABLED", "true").lower() == "true"
    )
    KNOWLEDGE_SEMANTIC_DEDUP_THRESHOLD = float(
        os.getenv("KNOWLEDGE_SEMANTIC_DEDUP_THRESHOLD", "0.92")
    )
    ADMIN_METRICS_MAX_HOURS = int(os.getenv("ADMIN_METRICS_MAX_HOURS", "720"))
    RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED = (
        os.getenv("RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED", "true").lower() == "true"
    )

    CHAT_ATTACHMENT_CONTEXT_ENABLED = (
        os.getenv("CHAT_ATTACHMENT_CONTEXT_ENABLED", "true").lower() == "true"
    )
    CHAT_ATTACHMENT_CONTEXT_MAX_CHARS = int(
        os.getenv("CHAT_ATTACHMENT_CONTEXT_MAX_CHARS", "6000")
    )
    CHAT_ATTACHMENT_IMAGE_OCR_ENABLED = (
        os.getenv("CHAT_ATTACHMENT_IMAGE_OCR_ENABLED", "false").lower() == "true"
    )
    CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS = int(
        os.getenv("CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS", "4000")
    )
    CHAT_DRAWING_PDF_MAX_PAGES = int(os.getenv("CHAT_DRAWING_PDF_MAX_PAGES", "10"))
    CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS = int(
        os.getenv("CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS", "40")
    )
    CHAT_DOCUMENT_VISION_ENABLED = (
        os.getenv("CHAT_DOCUMENT_VISION_ENABLED", "false").lower() == "true"
    )
    CHAT_DOCUMENT_VISION_BACKEND = os.getenv("CHAT_DOCUMENT_VISION_BACKEND", "auto").strip().lower()
    CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = (
        os.getenv("CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING", "true").lower() == "true"
    )
    CHAT_DOCUMENT_VISION_MAX_PAGES = int(
        os.getenv("CHAT_DOCUMENT_VISION_MAX_PAGES", os.getenv("CHAT_DRAWING_PDF_MAX_PAGES", "10"))
    )
    CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS = int(
        os.getenv(
            "CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS",
            os.getenv("CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS", "40"),
        )
    )
    CHAT_DOCUMENT_VISION_DPI = int(os.getenv("CHAT_DOCUMENT_VISION_DPI", "200"))
    CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS = float(
        os.getenv("CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS", "120")
    )
    CHAT_DOCUMENT_VISION_MAX_CHARS = int(
        os.getenv(
            "CHAT_DOCUMENT_VISION_MAX_CHARS",
            os.getenv("CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS", "8000"),
        )
    )
    CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED = (
        os.getenv("CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED", "true").lower() == "true"
    )
    CHAT_DOCUMENT_VISION_TESSERACT_LANG = os.getenv(
        "CHAT_DOCUMENT_VISION_TESSERACT_LANG",
        "por+eng",
    ).strip()
    CHAT_DOCUMENT_VISION_OLLAMA_MODEL = os.getenv(
        "CHAT_DOCUMENT_VISION_OLLAMA_MODEL",
        "qwen2.5vl:7b",
    ).strip()
    CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL = os.getenv(
        "CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL",
        "",
    ).strip()
    # Com backend=auto: tenta qwen2.5vl após Tesseract se o texto ainda for insuficiente.
    CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK = (
        os.getenv("CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK", "true").lower() == "true"
    )
    CHAT_RESPONSE_MODES_ENABLED = (
        os.getenv("CHAT_RESPONSE_MODES_ENABLED", "true").lower() == "true"
    )

    EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED = (
        os.getenv("EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED", "true").lower() == "true"
    )
    EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT = int(
        os.getenv("EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT", "40")
    )
    EXTERNAL_ACTION_SEMANTIC_MIN_SCORE = float(
        os.getenv("EXTERNAL_ACTION_SEMANTIC_MIN_SCORE", "0.42")
    )

    CHAT_TOOL_ROUTER_ENABLED = (
        os.getenv("CHAT_TOOL_ROUTER_ENABLED", "false").lower() == "true"
    )
    CHAT_FAST_PATH_ENABLED = (
        os.getenv("CHAT_FAST_PATH_ENABLED", "true").lower() == "true"
    )
    CHAT_FAST_PATH_MAX_CHARS = int(os.getenv("CHAT_FAST_PATH_MAX_CHARS", "30"))
    CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED = (
        os.getenv("CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED", "true").lower()
        == "true"
    )
    # Homologação local: api-delpi costuma estar off; prioriza rotas api_externa.* na seleção.
    CHAT_PREFER_API_EXTERNA_PROVIDER = (
        os.getenv("CHAT_PREFER_API_EXTERNA_PROVIDER", "false").lower() == "true"
    )
    CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS = int(
        os.getenv("CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS", "2")
    )
    CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS = float(
        os.getenv("CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS", "45")
    )
    CHAT_PERSIST_BEFORE_PLAYBACK = (
        os.getenv("CHAT_PERSIST_BEFORE_PLAYBACK", "true").lower() == "true"
    )
    CHAT_OPERATIONAL_FAST_PATH_ENABLED = (
        os.getenv("CHAT_OPERATIONAL_FAST_PATH_ENABLED", "true").lower() == "true"
    )
    CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED = (
        os.getenv("CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED", "true").lower() == "true"
    )
    CHAT_UTILITY_DIRECT_ENABLED = (
        os.getenv("CHAT_UTILITY_DIRECT_ENABLED", "true").lower() == "true"
    )
    CHAT_UTILITY_TIMEZONE = os.getenv(
        "CHAT_UTILITY_TIMEZONE",
        os.getenv("TZ", "America/Sao_Paulo"),
    ).strip()
    CHAT_USER_CONTEXT_ENABLED = (
        os.getenv("CHAT_USER_CONTEXT_ENABLED", "true").lower() == "true"
    )
    CHAT_DEFAULT_SQL_AUTHORING_SKILL = (
        os.getenv("CHAT_DEFAULT_SQL_AUTHORING_SKILL", "true").lower() == "true"
    )
    CHAT_DEFAULT_SQL_DIALECT = os.getenv("CHAT_DEFAULT_SQL_DIALECT", "sqlserver").strip().lower()
    CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL = (
        os.getenv("CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL", "true").lower() == "true"
    )
    CHAT_PLATFORM_DEFAULT_AGENT_ENABLED = (
        os.getenv("CHAT_PLATFORM_DEFAULT_AGENT_ENABLED", "true").lower() == "true"
    )
    CHAT_PLATFORM_DEFAULT_AGENT_ID = os.getenv("CHAT_PLATFORM_DEFAULT_AGENT_ID", "").strip()
    CHAT_PLATFORM_DEFAULT_AGENT_NAME = os.getenv(
        "CHAT_PLATFORM_DEFAULT_AGENT_NAME",
        "Agente Minha DELPI",
    ).strip()
    CHAT_TOOL_ROUTER_MAX_ACTIONS = int(os.getenv("CHAT_TOOL_ROUTER_MAX_ACTIONS", "20"))

    CHAT_HISTORY_SUMMARY_ENABLED = (
        os.getenv("CHAT_HISTORY_SUMMARY_ENABLED", "true").lower() == "true"
    )
    CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES = int(
        os.getenv("CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES", "16")
    )
    CHAT_HISTORY_SUMMARY_MAX_CHARS = int(
        os.getenv("CHAT_HISTORY_SUMMARY_MAX_CHARS", "1500")
    )

    EXTERNAL_ACTION_EMBEDDING_ON_IMPORT = (
        os.getenv("EXTERNAL_ACTION_EMBEDDING_ON_IMPORT", "true").lower() == "true"
    )

    CHAT_RAG_HYBRID_ENABLED = (
        os.getenv("CHAT_RAG_HYBRID_ENABLED", "true").lower() == "true"
    )
    CHAT_RAG_PREFER_KEYWORD_SEARCH = (
        os.getenv("CHAT_RAG_PREFER_KEYWORD_SEARCH", "true").lower() == "true"
    )
    CHAT_RAG_HYBRID_VECTOR_WEIGHT = float(
        os.getenv("CHAT_RAG_HYBRID_VECTOR_WEIGHT", "0.7")
    )
    CHAT_RAG_HYBRID_KEYWORD_WEIGHT = float(
        os.getenv("CHAT_RAG_HYBRID_KEYWORD_WEIGHT", "0.3")
    )
    CHAT_RAG_HYBRID_CANDIDATE_MULTIPLIER = int(
        os.getenv("CHAT_RAG_HYBRID_CANDIDATE_MULTIPLIER", "4")
    )

    EMBEDDING_CACHE_ENABLED = (
        os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
    )
    EMBEDDING_CACHE_BACKEND = os.getenv("EMBEDDING_CACHE_BACKEND", "memory")
    EMBEDDING_CACHE_TTL_SECONDS = int(os.getenv("EMBEDDING_CACHE_TTL_SECONDS", "3600"))
    EMBEDDING_CACHE_MAX_ENTRIES = int(os.getenv("EMBEDDING_CACHE_MAX_ENTRIES", "500"))
    REDIS_URL = os.getenv("REDIS_URL", "").strip() or None

    CHAT_MULTI_ACTION_ENABLED = (
        os.getenv("CHAT_MULTI_ACTION_ENABLED", "true").lower() == "true"
    )
    CHAT_MULTI_ACTION_MAX_CALLS = int(os.getenv("CHAT_MULTI_ACTION_MAX_CALLS", "5"))

    CHAT_PAGINATION_AUTO_FETCH_ENABLED = (
        os.getenv("CHAT_PAGINATION_AUTO_FETCH_ENABLED", "true").lower() == "true"
    )
    CHAT_PAGINATION_MAX_PAGES_PER_TURN = int(
        os.getenv("CHAT_PAGINATION_MAX_PAGES_PER_TURN", "5")
    )

    CHAT_AGENTIC_LOOP_ENABLED = (
        os.getenv("CHAT_AGENTIC_LOOP_ENABLED", "false").lower() == "true"
    )
    CHAT_AGENTIC_LOOP_MAX_STEPS = int(os.getenv("CHAT_AGENTIC_LOOP_MAX_STEPS", "2"))
    CHAT_AGENTIC_CATALOG_MAX_ACTIONS = int(
        os.getenv("CHAT_AGENTIC_CATALOG_MAX_ACTIONS", "12")
    )
    CHAT_AGENTIC_SCHEMA_MAX_PARAMETERS = int(
        os.getenv("CHAT_AGENTIC_SCHEMA_MAX_PARAMETERS", "10")
    )

    CHAT_RAG_RERANK_ENABLED = (
        os.getenv("CHAT_RAG_RERANK_ENABLED", "true").lower() == "true"
    )
    CHAT_RAG_RERANK_KEYWORD_BOOST = float(
        os.getenv("CHAT_RAG_RERANK_KEYWORD_BOOST", "0.15")
    )
    CHAT_RAG_FTS_ENABLED = (
        os.getenv("CHAT_RAG_FTS_ENABLED", "true").lower() == "true"
    )

    CHAT_NATIVE_TOOL_CALLING_ENABLED = (
        os.getenv("CHAT_NATIVE_TOOL_CALLING_ENABLED", "false").lower() == "true"
    )
    CHAT_WEB_SEARCH_ENABLED = (
        os.getenv("CHAT_WEB_SEARCH_ENABLED", "false").lower() == "true"
    )
    CHAT_WEB_SEARCH_MAX_RESULTS = int(os.getenv("CHAT_WEB_SEARCH_MAX_RESULTS", "5"))
    CHAT_WEB_SEARCH_TIMEOUT_SECONDS = float(
        os.getenv("CHAT_WEB_SEARCH_TIMEOUT_SECONDS", "8")
    )
    CHAT_WEB_SEARCH_PROVIDER = os.getenv("CHAT_WEB_SEARCH_PROVIDER", "auto").lower().strip()
    CHAT_WEB_SEARCH_RETRY_EN = (
        os.getenv("CHAT_WEB_SEARCH_RETRY_EN", "true").lower() == "true"
    )
    CHAT_WEB_SEARCH_TAVILY_API_KEY = os.getenv("CHAT_WEB_SEARCH_TAVILY_API_KEY", "").strip()
    CHAT_WEB_SEARCH_SERPER_API_KEY = os.getenv("CHAT_WEB_SEARCH_SERPER_API_KEY", "").strip()
    CHAT_WEB_SEARCH_BING_API_KEY = os.getenv("CHAT_WEB_SEARCH_BING_API_KEY", "").strip()
    CHAT_WEB_SEARCH_SEARXNG_BASE_URL = os.getenv(
        "CHAT_WEB_SEARCH_SEARXNG_BASE_URL",
        "",
    ).strip()
    CHAT_WEB_SEARCH_SEARXNG_LANGUAGE = os.getenv(
        "CHAT_WEB_SEARCH_SEARXNG_LANGUAGE",
        "pt-BR",
    ).strip()
    CHAT_WEB_SEARCH_SEARXNG_CATEGORIES = os.getenv(
        "CHAT_WEB_SEARCH_SEARXNG_CATEGORIES",
        "general",
    ).strip()
    CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED = (
        os.getenv("CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED", "true").lower() == "true"
    )
    CHAT_WEB_SEARCH_SYNTHESIS_ENABLED = (
        os.getenv("CHAT_WEB_SEARCH_SYNTHESIS_ENABLED", "true").lower() == "true"
    )
    CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS = int(
        os.getenv("CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS", "2")
    )

    @classmethod
    def resolve_web_search_provider(cls) -> str:
        provider = cls.CHAT_WEB_SEARCH_PROVIDER

        if provider in {"", "auto"}:
            return "auto"

        allowed = {"duckduckgo", "tavily", "serper", "bing", "searxng"}

        if provider in allowed:
            return provider

        return "auto"

    OLLAMA_WARMUP_ON_STARTUP = (
        os.getenv("OLLAMA_WARMUP_ON_STARTUP", "true").lower() == "true"
    )
    CHAT_FAST_PATH_SLIM_PROMPT = (
        os.getenv("CHAT_FAST_PATH_SLIM_PROMPT", "true").lower() == "true"
    )
    # Modo operacional: não injeta perfil RBAC completo no system prompt (menos tokens/latência).
    CHAT_OPERATIONAL_SLIM_USER_CONTEXT = (
        os.getenv("CHAT_OPERATIONAL_SLIM_USER_CONTEXT", "true").lower() == "true"
    )

    LGPD_REQUIRE_AI_CONSENT = (
        os.getenv("LGPD_REQUIRE_AI_CONSENT", "true").lower() == "true"
    )