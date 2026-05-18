import os


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
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
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

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))

    VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
    VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    VLLM_API_KEY = os.getenv("VLLM_API_KEY", "minha-delpi-local-vllm")
    VLLM_TIMEOUT_SECONDS = float(os.getenv("VLLM_TIMEOUT_SECONDS", "300"))

    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "120"))

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
    MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "6"))
    MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "9000"))

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
        os.getenv("KNOWLEDGE_DOCUMENT_MAX_CHARS", "50000")
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
        os.getenv("CHAT_TOOL_ROUTER_ENABLED", "true").lower() == "true"
    )
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
    EMBEDDING_CACHE_TTL_SECONDS = int(os.getenv("EMBEDDING_CACHE_TTL_SECONDS", "3600"))
    EMBEDDING_CACHE_MAX_ENTRIES = int(os.getenv("EMBEDDING_CACHE_MAX_ENTRIES", "500"))

    CHAT_AGENTIC_LOOP_ENABLED = (
        os.getenv("CHAT_AGENTIC_LOOP_ENABLED", "false").lower() == "true"
    )
    CHAT_AGENTIC_LOOP_MAX_STEPS = int(os.getenv("CHAT_AGENTIC_LOOP_MAX_STEPS", "2"))

    CHAT_RAG_RERANK_ENABLED = (
        os.getenv("CHAT_RAG_RERANK_ENABLED", "true").lower() == "true"
    )
    CHAT_RAG_RERANK_KEYWORD_BOOST = float(
        os.getenv("CHAT_RAG_RERANK_KEYWORD_BOOST", "0.15")
    )
    CHAT_RAG_FTS_ENABLED = (
        os.getenv("CHAT_RAG_FTS_ENABLED", "true").lower() == "true"
    )