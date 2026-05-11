import os


class Settings:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "minha-delpi-ai-api")
    ENV = os.getenv("FLASK_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
