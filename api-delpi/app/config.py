import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Banco de Dados
    DB_HOST: str = os.getenv("DB_HOST")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_DATABASE: str = os.getenv("DB_DATABASE")
    DB_PORT: str = os.getenv("DB_PORT", "1433")

    # API Server
    PORT: str = os.getenv("PORT", "8000")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")

    KEYCLOAK_JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL")
    KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE")

    # Configurações de execução do agente GPT
    AUTO_EXECUTE_API: bool = os.getenv("AUTO_EXECUTE_API", "true").lower() == "true"
    CONFIRM_BEFORE_REQUEST: bool = os.getenv("CONFIRM_BEFORE_REQUEST", "false").lower() == "true"
    SHOW_PAYLOAD_BEFORE_EXECUTE: bool = os.getenv("SHOW_PAYLOAD_BEFORE_EXECUTE", "false").lower() == "true"

settings = Settings()
