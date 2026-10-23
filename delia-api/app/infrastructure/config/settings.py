from __future__ import annotations

import ipaddress
import os
import urllib.parse


_ENV_FLAG_TRUE = frozenset({"1", "true", "yes", "on"})
_ENV_FLAG_FALSE = frozenset({"0", "false", "no", "off"})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _ENV_FLAG_TRUE


# C3-OLLAMA-LOCAL-LLM-TESTING-01: outside production the configured LLM
# endpoint must resolve to a local runtime (Ollama). ``production`` is the
# only environment allowed to reach an external model provider.
_LOCAL_LLM_HOSTNAMES = frozenset(
    {"localhost", "ollama", "host.docker.internal", "host.containers.internal"}
)


def is_local_llm_host(host: str) -> bool:
    """True for loopback/non-global IPs and internal service hostnames."""
    normalized = (host or "").strip().strip("[]").lower()
    if not normalized:
        return False
    if normalized in _LOCAL_LLM_HOSTNAMES:
        return True
    try:
        return not ipaddress.ip_address(normalized).is_global
    except ValueError:
        # Bare compose-style service names resolve only inside the
        # internal network; any dotted hostname may be a public DNS name.
        return "." not in normalized


def llm_egress_blocked_reason(environment: str, base_url: str) -> str | None:
    """Return why ``base_url`` is refused, or ``None`` when it is allowed."""
    if environment == "production" or not base_url:
        return None
    host = urllib.parse.urlsplit(base_url).hostname or ""
    if is_local_llm_host(host):
        return None
    return (
        "external LLM endpoint refused outside production "
        f"(DELIA_ENV={environment}): host {host!r} is not a local "
        "runtime address"
    )


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
        # Optional provider-side output cap. Some providers reserve the
        # model's maximum output against the account balance when
        # max_tokens is absent, rejecting requests intermittently; a
        # configured ceiling keeps the reservation bounded.
        llm_max_output_tokens = (
            os.getenv("DELIA_LLM_MAX_OUTPUT_TOKENS") or ""
        ).strip()
        self.llm_max_output_tokens = (
            int(llm_max_output_tokens) if llm_max_output_tokens else None
        )
        # C3-OLLAMA-LOCAL-LLM-TESTING-01: when set, no real provider may be
        # wired — the configured endpoint is external and this environment
        # is not production. Composition stays fail-closed and eval
        # scripts must refuse before opening any socket.
        self.llm_egress_blocked_reason = llm_egress_blocked_reason(
            environment=self.environment, base_url=self.llm_base_url
        )
        # Doc 103 (approved): per-LLM-call budget for every model stage
        # inside a turn — at most 60 real inference seconds per logical
        # call, always clamped against the interaction deadline. Kept
        # aligned with the provider timeout below it: the stage cap must
        # never cut a legitimate call that the provider could still
        # answer inside its own ceiling.
        self.model_stage_timeout_seconds = float(
            os.getenv("DELIA_MODEL_STAGE_TIMEOUT_SECONDS") or "60.0"
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
        # CRI E1 (doc 73 §7 / spec 75 §4.1): single central switch for
        # the conversational response-intelligence front. Absent and
        # invalid values fail closed to baseline; this is a behavior
        # switch resolved once at composition — never an authorization,
        # never read from request/model/provider/frontend state.
        _cri_raw = os.getenv("DELIA_RESPONSE_INTELLIGENCE_ENABLED")
        self.response_intelligence_enabled = _env_flag(
            "DELIA_RESPONSE_INTELLIGENCE_ENABLED"
        )
        self.response_intelligence_config_source = (
            "environment" if _cri_raw is not None else "default"
        )
        _cri_norm = _cri_raw.strip().lower() if _cri_raw is not None else None
        self.response_intelligence_config_invalid = (
            _cri_norm is not None
            and _cri_norm not in _ENV_FLAG_TRUE
            and _cri_norm not in _ENV_FLAG_FALSE
        )
        # Runtime build identity for incident correlation — `unknown`
        # when not reliably provided; never an error source.
        self.runtime_sha = (
            os.getenv("DELIA_RUNTIME_SHA") or ""
        ).strip() or "unknown"
        self.openapi_delpi_base_url = (
            os.getenv("DELIA_OPENAPI_DELPI_BASE_URL") or ""
        ).strip()
        self.openapi_delpi_declarations_path = (
            os.getenv("DELIA_OPENAPI_DELPI_DECLARATIONS_PATH") or ""
        ).strip()
        self.openapi_timeout_seconds = float(
            os.getenv("DELIA_OPENAPI_TIMEOUT_SECONDS") or "15.0"
        )
        # LOOP-03R2A / Stage 05 / doc 103: wall-clock budget for one
        # interaction turn, shared by every governed stage. Under the
        # approved 60s-per-LLM-call policy the turn deadline equals the
        # monotonic global cap — 300s anchored at request start, never
        # reset between stages, calls or retries. Stages are
        # reduction-clamped only.
        self.turn_budget_seconds = float(
            os.getenv("DELIA_TURN_BUDGET_SECONDS") or "300.0"
        )
        # CP4 governed stage resume (docs 88 §10.2 / 90): OFF by
        # default — a single attempt is the legacy behavior; setting
        # 2 enables one bounded governed re-attempt of the whole turn
        # under the remaining global budget (never a per-LLM-call
        # retry — that inner mechanism is separate, doc 103).
        self.max_governed_attempts = int(
            os.getenv("DELIA_MAX_GOVERNED_ATTEMPTS") or "1"
        )
        self.interaction_total_budget_seconds = float(
            os.getenv("DELIA_INTERACTION_TOTAL_BUDGET_SECONDS")
            or "300.0"
        )
        # VD-F03 dictation.transcription.v1 — dedicated audio-capable
        # model behind the same approved OpenAI-compatible provider
        # family. Independent DELIA_STT_* set: incomplete config fails
        # closed (dictation status unavailable); stt_api_key is never
        # logged or repr'd.
        self.stt_provider = (os.getenv("DELIA_STT_PROVIDER") or "").strip()
        self.stt_base_url = (os.getenv("DELIA_STT_BASE_URL") or "").strip()
        self.stt_model = (os.getenv("DELIA_STT_MODEL") or "").strip()
        self.stt_api_key = (os.getenv("DELIA_STT_API_KEY") or "").strip()
        self.stt_timeout_seconds = float(
            os.getenv("DELIA_STT_TIMEOUT_SECONDS") or "30.0"
        )
        self.stt_max_audio_bytes = int(
            os.getenv("DELIA_STT_MAX_AUDIO_BYTES") or "8388608"
        )
        self.stt_max_duration_ms = int(
            os.getenv("DELIA_STT_MAX_DURATION_MS") or "300000"
        )
        self.stt_rate_limit_per_minute = int(
            os.getenv("DELIA_STT_RATE_LIMIT_PER_MINUTE") or "10"
        )


    @classmethod
    def for_testing(cls) -> "Settings":
        settings = cls()
        settings.environment = "testing"
        settings.debug = False
        settings.log_level = "WARNING"
        return settings
