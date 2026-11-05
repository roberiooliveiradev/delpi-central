from __future__ import annotations

import ipaddress
import os
import urllib.parse
from pathlib import Path

from app.infrastructure.config.pydantic_ai_runtime_config import (
    PydanticAiRuntimeConfig,
    load_pydantic_ai_runtime_config,
)


_ENV_FLAG_TRUE = frozenset({"1", "true", "yes", "on"})
_ENV_FLAG_FALSE = frozenset({"0", "false", "no", "off"})

# Doc 243: unified non-secret Pydantic AI runtime tuning artifact —
# fixed repo path, never request/env-supplied. Loaded fail-closed.
_RUNTIME_CONFIG_PATH = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "pydantic_ai.runtime.delpi.json"
)

# Doc 243 §4/§6: environment variables whose authority moved to the
# single runtime JSON. An explicitly set non-empty value is stale
# configuration and fails closed — never a silent second source.
_RETIRED_LLM_ENV_VARS = frozenset(
    {
        "DELIA_LLM_PROVIDER",
        "DELIA_LLM_MODEL",
        "DELIA_LLM_TIMEOUT_SECONDS",
        "DELIA_LLM_MAX_OUTPUT_TOKENS",
        "DELIA_LLM_CONTEXT_TOKENS",
        "DELIA_MODEL_STAGE_TIMEOUT_SECONDS",
        "DELIA_TURN_BUDGET_SECONDS",
        "DELIA_INTERACTION_TOTAL_BUDGET_SECONDS",
        "DELIA_MAX_GOVERNED_ATTEMPTS",
        "DELIA_LLM_CALL_MAX_ATTEMPTS",
    }
)


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
        # Doc 243: every migrated tuning env fails closed when
        # explicitly set — the single runtime JSON owns them now.
        for retired in sorted(_RETIRED_LLM_ENV_VARS):
            stale = os.getenv(retired)
            if stale is not None and stale.strip():
                raise ValueError(
                    f"{retired} is retired: intelligence tuning lives "
                    "in config/pydantic_ai.runtime.delpi.json — unset "
                    "the variable"
                )
        # Doc 243: the legacy model runtime is removed. The variable is
        # retired — only the single supported value is a harmless
        # no-op; every explicit obsolete choice fails closed, never a
        # fallback.
        _retired_model_runtime = (
            (os.getenv("DELIA_MODEL_RUNTIME") or "").strip().lower()
        )
        if _retired_model_runtime and _retired_model_runtime != (
            "pydantic_ai"
        ):
            raise ValueError(
                "DELIA_MODEL_RUNTIME is retired: pydantic_ai is the "
                f"only intelligence runtime, got "
                f"{_retired_model_runtime!r}"
            )
        # Doc 243: ONE validated non-secret JSON snapshot supplies all
        # intelligence tunables. Secrets/transport (base URL, API key)
        # remain environment bindings — never in the artifact.
        runtime_config: PydanticAiRuntimeConfig = (
            load_pydantic_ai_runtime_config(
                _RUNTIME_CONFIG_PATH,
                profile_selector=(
                    os.getenv("DELIA_RUNTIME_PROFILE") or ""
                ).strip(),
            )
        )
        self.runtime_config = runtime_config
        _profile = runtime_config.profile
        self.runtime_profile = runtime_config.profile_name
        self.runtime_config_fingerprint = runtime_config.fingerprint
        # Real-provider gate (C3-IR-01R2). Incomplete secret/transport
        # config fails closed — never log or repr llm_api_key.
        self.llm_provider = _profile.model.provider
        self.llm_base_url = (os.getenv("DELIA_LLM_BASE_URL") or "").strip()
        self.llm_model = _profile.model.model_name
        self.llm_api_key = (os.getenv("DELIA_LLM_API_KEY") or "").strip()
        self.llm_timeout_seconds = (
            _profile.budgets.provider_call_timeout_seconds
        )
        # Optional provider-side output cap. Some providers reserve the
        # model's maximum output against the account balance when
        # max_tokens is absent, rejecting requests intermittently; a
        # configured ceiling keeps the reservation bounded. ``None`` =
        # unconfigured, never "unlimited".
        self.llm_max_output_tokens = (
            _profile.generation.max_output_tokens
        )
        # Declared effective input window in tokens — the runtime value
        # the provider actually honors (e.g. server-configured num_ctx),
        # never the model's nominal capacity. ``None`` → unknown →
        # pre-call budget enforcement stays off rather than guessing.
        self.llm_context_tokens = (
            _profile.context.effective_context_window_tokens
        )
        # Governed per-LLM-call budgets (doc 103): the stage cap may
        # never outlive the turn deadline; the interaction cap is the
        # monotonic total across governed attempts.
        self.model_stage_timeout_seconds = (
            _profile.budgets.model_stage_timeout_seconds
        )
        self.turn_budget_seconds = (
            _profile.budgets.turn_budget_seconds
        )
        self.interaction_total_budget_seconds = (
            _profile.budgets.interaction_total_budget_seconds
        )
        self.max_governed_attempts = (
            _profile.budgets.max_governed_attempts
        )
        # Doc 103 GATE 1: per-LOGICAL-CALL retry limit — the JSON value
        # is already clamped to the PO-approved ceiling at load time.
        self.llm_call_max_attempts = _profile.agent.llm_call_max_attempts
        # General interaction-path per-call cap (the non-orchestration
        # model call) — previously a hidden Python constant.
        self.interaction_call_timeout_seconds = (
            _profile.budgets.interaction_call_timeout_seconds
        )
        # Pydantic AI investigation runtime knobs.
        self.agent_request_limit = _profile.agent.request_limit
        self.agent_tool_calls_limit = _profile.agent.tool_calls_limit
        self.agent_retries = _profile.agent.retries
        self.tool_result_max_projection_chars = (
            _profile.tool_results.max_projection_chars
        )
        self.prior_turns_limit = _profile.context.prior_turns_limit
        self.prior_turn_max_chars = _profile.context.prior_turn_max_chars
        self.observability_record_model_id = (
            _profile.observability.record_model_id
        )
        self.observability_record_usage = (
            _profile.observability.record_usage
        )
        self.observability_record_config_fingerprint = (
            _profile.observability.record_config_fingerprint
        )
        # C3-OLLAMA-LOCAL-LLM-TESTING-01: when set, no real provider may be
        # wired — the configured endpoint is external and this environment
        # is not production. Composition stays fail-closed and eval
        # scripts must refuse before opening any socket.
        self.llm_egress_blocked_reason = llm_egress_blocked_reason(
            environment=self.environment, base_url=self.llm_base_url
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
            "caio": (os.getenv("DELIA_MCP_CAIO_BASE_URL") or "").strip(),
            "clara": (os.getenv("DELIA_MCP_CLARA_BASE_URL") or "").strip(),
            "suri": (os.getenv("DELIA_MCP_SURI_BASE_URL") or "").strip(),
            "eva": (os.getenv("DELIA_MCP_EVA_BASE_URL") or "").strip(),
        }
        self.mcp_specialist_enabled = {
            "davi": _env_flag("DELIA_MCP_DAVI_ENABLED"),
            "teo": _env_flag("DELIA_MCP_TEO_ENABLED"),
            "vista": _env_flag("DELIA_MCP_VISTA_ENABLED"),
            "caio": _env_flag("DELIA_MCP_CAIO_ENABLED"),
            "clara": _env_flag("DELIA_MCP_CLARA_ENABLED"),
            "suri": _env_flag("DELIA_MCP_SURI_ENABLED"),
            "eva": _env_flag("DELIA_MCP_EVA_ENABLED"),
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
        # DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-01: the direct DELPI
        # OpenAPI source binding (env-enabled provider + governed
        # declarations file) is removed entirely — DELPI domain data
        # reaches DÉLIA exclusively through DAVI/MCP.
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
        # DELIA_OPENAPI_TIMEOUT_SECONDS removed with the direct source
        # wiring — no OpenAPI source is composed from settings anymore.
        # Doc 231+241: production orchestration-engine selection —
        # backend-controlled config ONLY; never request/model/
        # provider-sourced. `pydantic_ai` is the only supported engine;
        # the `delia` Application sequencer rollback is retired (the
        # semantic engine it selected no longer exists).
        self.orchestration_engine = (
            os.getenv("DELIA_ORCHESTRATION_ENGINE") or "pydantic_ai"
        ).strip()
        # Doc 231: LangGraph Send fan-out retired — flag retained only
        # so composition can fail closed when stale env enables it.
        self.subobjective_fanout_enabled = _env_flag(
            "DELIA_SUBOBJECTIVE_FANOUT"
        )
        # Doc 231: LangGraph SqliteSaver retired — non-empty path fails
        # closed at composition.
        self.checkpoint_db_path = (
            os.getenv("DELIA_CHECKPOINT_DB") or ""
        ).strip() or None
        # Doc 216: isolated catalog experiment — LIVE default;
        # SNAPSHOT_EXPERIMENT is eval-only composition config.
        self.mcp_catalog_mode = (
            os.getenv("DELIA_MCP_CATALOG_MODE") or "live"
        ).strip().lower()
        self.mcp_catalog_db = (
            os.getenv("DELIA_MCP_CATALOG_DB") or ""
        ).strip() or None
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
        # VD-F06 dictation.incremental.v1 — segmented live sessions.
        # Disabled by default; activation happens only through the
        # admission gate after deploy (flag OFF → smoke → flag ON).
        self.stt_incremental_enabled = (
            os.getenv("DELIA_STT_INCREMENTAL_ENABLED") or ""
        ).strip() == "1"
        self.stt_incremental_max_session_ms = int(
            os.getenv("DELIA_STT_INCREMENTAL_MAX_SESSION_MS") or "300000"
        )
        self.stt_incremental_max_segment_ms = int(
            os.getenv("DELIA_STT_INCREMENTAL_MAX_SEGMENT_MS") or "15000"
        )
        self.stt_incremental_max_segments = int(
            os.getenv("DELIA_STT_INCREMENTAL_MAX_SEGMENTS") or "120"
        )
        self.stt_incremental_max_segment_bytes = int(
            os.getenv("DELIA_STT_INCREMENTAL_MAX_SEGMENT_BYTES")
            or "1500000"
        )
        self.stt_incremental_max_in_flight = int(
            os.getenv("DELIA_STT_INCREMENTAL_MAX_IN_FLIGHT") or "4"
        )


    @classmethod
    def for_testing(cls) -> "Settings":
        settings = cls()
        settings.environment = "testing"
        settings.debug = False
        settings.log_level = "WARNING"
        return settings
