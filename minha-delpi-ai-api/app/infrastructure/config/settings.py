import os


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "minha-delpi-ai-api")
    ENV = os.getenv("FLASK_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://plugins_user:plugins_password@postgres-plugins:5432/plugins_hub",
    )

    KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "")
    KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "")
    JWT_ALGORITHMS = os.getenv("JWT_ALGORITHMS", "RS256")

    CORE_API_BASE_URL = os.getenv("CORE_API_BASE_URL", "http://core-api:8000")
    CORE_API_TIMEOUT_SECONDS = float(os.getenv("CORE_API_TIMEOUT_SECONDS", "5"))

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

    CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "12"))
