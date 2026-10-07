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
        # VISTA only). Static global user tokens were removed in R1A —
        # credentials are per-request delegated tokens, never config.
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
        # C3-MCP-INTEROP-01R1A: user-delegated identity via a single
        # confidential DÉLIA requester client + RFC 8693 token exchange.
        # The secret is runtime config only — never logged, never
        # persisted, never propagated into contracts or model context.
        keycloak_url = (os.getenv("KEYCLOAK_URL") or "").strip().rstrip("/")
        keycloak_realm = (os.getenv("KEYCLOAK_REALM") or "").strip()
        self.exchange_token_url = (
            os.getenv("DELIA_TOKEN_EXCHANGE_URL") or ""
        ).strip() or (
            f"{keycloak_url}/realms/{keycloak_realm}"
            "/protocol/openid-connect/token"
            if keycloak_url and keycloak_realm
            else ""
        )
        self.exchange_client_id = (
            os.getenv("DELIA_EXCHANGE_CLIENT_ID") or "delia-api"
        ).strip()
        self.exchange_client_secret = (
            os.getenv("DELIA_EXCHANGE_CLIENT_SECRET") or ""
        ).strip()
        self.exchange_timeout_seconds = float(
            os.getenv("DELIA_EXCHANGE_TIMEOUT_SECONDS") or "10.0"
        )
        # Issuer Host header: the token endpoint may be reached through
        # an internal URL while Keycloak derives `iss` from the request
        # Host. Must match the public issuer so subject-token validation
        # and exchanged-token `iss` are consistent.
        from urllib.parse import urlsplit

        issuer = (os.getenv("KEYCLOAK_ISSUER") or "").strip()
        self.exchange_host_header = (
            os.getenv("DELIA_EXCHANGE_HOST_HEADER")
            or urlsplit(issuer).netloc
            or ""
        ).strip()
        # Delegated-token reuse bound: default 120s, hard cap 300s.
        self.delegated_token_ttl_seconds = min(
            float(
                os.getenv("DELIA_MCP_DELEGATED_TOKEN_TTL_SECONDS")
                or "120.0"
            ),
            300.0,
        )
        # ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (§6.130):
        # OpenAPI is one provider family. A source activates only with
        # complete config: base URL + a governed declarations file.
        # Missing pieces fail closed — no implicit surface.
        self.openapi_delpi_enabled = _env_flag(
            "DELIA_OPENAPI_DELPI_ENABLED"
        )
        self.openapi_delpi_base_url = (
            os.getenv("DELIA_OPENAPI_DELPI_BASE_URL") or ""
        ).strip()
        self.openapi_delpi_declarations_path = (
            os.getenv("DELIA_OPENAPI_DELPI_DECLARATIONS_PATH") or ""
        ).strip()
        self.openapi_timeout_seconds = float(
            os.getenv("DELIA_OPENAPI_TIMEOUT_SECONDS") or "15.0"
        )
        # LOOP-03R2A: total wall-clock budget for ONE interaction turn,
        # shared by every governed stage (model calls, provider calls).
        # Default 80s keeps a >=20s margin under the ~100s edge
        # (Cloudflare proxy) timeout observed as 524 in production —
        # the application always answers first with a deterministic
        # bounded result.
        self.turn_budget_seconds = float(
            os.getenv("DELIA_TURN_BUDGET_SECONDS") or "80.0"
        )


    @classmethod
    def for_testing(cls) -> "Settings":
        settings = cls()
        settings.environment = "testing"
        settings.debug = False
        settings.log_level = "WARNING"
        return settings
