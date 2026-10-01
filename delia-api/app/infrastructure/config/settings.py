from __future__ import annotations

import os


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Process settings. JWT secrets are not stored here — only public config refs."""

    def __init__(self) -> None:
        self.service_name = os.getenv("SERVICE_NAME", "delia-api")
        self.service_version = os.getenv("SERVICE_VERSION", "0.0.1")
        self.environment = os.getenv("DELIA_ENV", os.getenv("ENV", "development"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.debug = _env_flag("DELIA_DEBUG", default=False)
        self.host = os.getenv("DELIA_API_HOST", "0.0.0.0")
        self.port = int(os.getenv("DELIA_API_PORT", "8000"))
        # Core effective-access transport (same conventions as delpi_auth FastAPI middleware).
        self.core_api_url = (
            os.getenv("DELPI_AUTH_CORE_API_URL")
            or os.getenv("CORE_API_URL")
            or ""
        ).strip()
        self.core_timeout_seconds = float(
            os.getenv("DELIA_CORE_TIMEOUT_SECONDS")
            or os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS")
            or "5.0"
        )
        # Real-provider gate (C3-IR-01R2). Incomplete config fails closed —
        # never log or repr llm_api_key.
        self.llm_provider = (os.getenv("DELIA_LLM_PROVIDER") or "").strip()
        self.llm_base_url = (os.getenv("DELIA_LLM_BASE_URL") or "").strip()
        self.llm_model = (os.getenv("DELIA_LLM_MODEL") or "").strip()
        self.llm_api_key = (os.getenv("DELIA_LLM_API_KEY") or "").strip()
        self.llm_timeout_seconds = float(
            os.getenv("DELIA_LLM_TIMEOUT_SECONDS") or "30.0"
        )
        # C3-MCP-INTEROP-01: approved specialist MCP connections (DAVI/TÉO/
        # VISTA only). *_USER_TOKEN is a user-delegated bearer for the
        # specialist MCP resource — never logged; absent token fails
        # closed at the adapter. There is no service-token path.
        self.mcp_timeout_seconds = float(
            os.getenv("DELIA_MCP_TIMEOUT_SECONDS") or "15.0"
        )
        self.mcp_specialist_endpoints = {
            "davi": (os.getenv("DELIA_MCP_DAVI_BASE_URL") or "").strip(),
            "teo": (os.getenv("DELIA_MCP_TEO_BASE_URL") or "").strip(),
            "vista": (os.getenv("DELIA_MCP_VISTA_BASE_URL") or "").strip(),
        }
        self.mcp_specialist_enabled = {
            "davi": _env_flag("DELIA_MCP_DAVI_ENABLED"),
            "teo": _env_flag("DELIA_MCP_TEO_ENABLED"),
            "vista": _env_flag("DELIA_MCP_VISTA_ENABLED"),
        }
        self.mcp_specialist_user_tokens = {
            key: (os.getenv(f"DELIA_MCP_{key.upper()}_USER_TOKEN") or "").strip()
            or None
            for key in ("davi", "teo", "vista")
        }

    @classmethod
    def for_testing(cls) -> "Settings":
        settings = cls()
        settings.environment = "testing"
        settings.debug = False
        settings.log_level = "WARNING"
        return settings
