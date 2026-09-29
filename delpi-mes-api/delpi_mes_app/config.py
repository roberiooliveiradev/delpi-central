import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    API_ROOT_PATH = os.getenv("DELPI_MES_API_ROOT_PATH", "/apps/delpi-mes-api")
    PORT = int(os.getenv("PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PRODUCTION_CONTROL_API_URL = os.getenv(
        "PRODUCTION_CONTROL_API_URL", "http://production-control-api:8000"
    ).rstrip("/")
    PRODUCTION_CONTROL_API_TIMEOUT = float(
        os.getenv("PRODUCTION_CONTROL_API_TIMEOUT", "5")
    )


settings = Settings()
