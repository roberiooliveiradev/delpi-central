from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
    ORCHESTRATION_INSTRUCTION_KEYS,
)
from app.application.interaction.handle_interactive_turn import (
    DEFAULT_MODEL_REF as DEFAULT_INTERACTION_MODEL_REF,
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import ModelRef
from app.infrastructure.http.bounded_request import bounded_request
from app.infrastructure.http.deadline_transport import (
    deadline_http_get,
    deadline_http_post,
)
from app.infrastructure.auth.core_platform_access import CorePlatformAccessAdapter
from app.infrastructure.config.settings import Settings
from app.infrastructure.config.cri_instruction_resource import (
    load_cri_presentation_vocabulary,
    load_orchestration_instructions,
)
from app.infrastructure.auth.subject_bearer import current_subject_bearer
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.logging import configure_logging
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.dictation_routes import register_dictation_routes
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.health_routes import health_bp
from app.interfaces.http.interaction_routes import register_interaction_routes
from app.interfaces.http.request_logging import register_request_logging

_logger = logging.getLogger(__name__)

# Doc 231+241: Pydantic AI unified investigation is the sole production
# orchestration runtime. The `delia` Application-sequencer rollback is
# retired — its semantic engine was removed; `delia`/LangGraph
# identifiers are rejected fail-closed.
_SUPPORTED_ORCHESTRATION_ENGINES = frozenset({"pydantic_ai"})


def _investigation_runtime_kwargs(settings: Settings) -> dict:
    """Map the validated runtime-config snapshot to the investigation
    orchestrator kwargs — the single source for agent/tool/projection
    tunables (doc 243)."""
    return {
        "request_limit": settings.agent_request_limit,
        "tool_calls_limit": settings.agent_tool_calls_limit,
        "agent_retries": settings.agent_retries,
        "tool_projection_limit": (
            settings.tool_result_max_projection_chars
        ),
        "prior_turns_limit": settings.prior_turns_limit,
        "prior_turn_max_chars": settings.prior_turn_max_chars,
    }


def _resolve_orchestration_attempt(
    engine_name: str,
    gates,
    *,
    investigation_model=None,
    investigation_model_factory=None,
    subobjective_fanout_enabled: bool = False,
    checkpoint_db_path: str | None = None,
    request_limit: int = 12,
    tool_calls_limit: int = 8,
    agent_retries: int = 1,
    tool_projection_limit: int = 6000,
    prior_turns_limit: int = 4,
    prior_turn_max_chars: int = 400,
):
    """Select ONE governed-attempt implementation for the composed
    application. Unknown identifiers fail closed — a misspelled
    engine must never silently select another engine.

    Doc 231+241: ``pydantic_ai`` is the unified investigation
    runtime and the only supported engine. Retired LangGraph flags
    (fan-out / checkpoint path) are accepted only as no-ops when
    empty/false so stale env files do not crash boot; non-empty
    checkpoint paths fail closed.
    """
    if engine_name not in _SUPPORTED_ORCHESTRATION_ENGINES:
        raise ValueError(
            "DELIA_ORCHESTRATION_ENGINE unsupported: "
            f"{engine_name!r} — expected one of "
            f"{sorted(_SUPPORTED_ORCHESTRATION_ENGINES)}"
        )
    if subobjective_fanout_enabled:
        raise ValueError(
            "DELIA_SUBOBJECTIVE_FANOUT is retired with LangGraph "
            "(doc 231) — unset the flag"
        )
    if checkpoint_db_path:
        raise ValueError(
            "DELIA_CHECKPOINT_DB is retired with LangGraph "
            "(doc 231) — unset the path"
        )
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )

    if investigation_model is None:
        raise ValueError(
            "pydantic_ai investigation runtime requires a "
            "composed model implementation"
        )
    return PydanticAiInvestigationOrchestrator(
        gates,
        model=investigation_model,
        model_factory=investigation_model_factory,
        request_limit=request_limit,
        tool_calls_limit=tool_calls_limit,
        agent_retries=agent_retries,
        tool_projection_limit=tool_projection_limit,
        prior_turns_limit=prior_turns_limit,
        prior_turn_max_chars=prior_turn_max_chars,
    )
# Governed declarative resource — fixed repo artifact, never a
# request/env-supplied path.
_CRI_PRESENTATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "cri_presentation.delpi.json"
)
# R1/M01: governed instruction resource — fixed repo artifact, never
# request/env-supplied. The orchestration surface is suppressed
# (fail-closed) when the resource is absent or invalid: a governed
# stage without its instruction text cannot run safely.
_ORCHESTRATION_INSTRUCTIONS_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "orchestration_instructions.delpi.json"
)


def _bounded_http_get(url: str, **kwargs):
    """``requests.get``-shaped GET under ONE absolute wall-clock deadline.

    Keeps the Core /me injection seam identical (callers still see a
    ``status_code``/``json()`` response) while DNS, connect, TLS,
    status line, headers and body share the proven bounded transport.
    """
    return bounded_request(
        deadline_http_get,
        url,
        headers=kwargs.get("headers"),
        timeout_seconds=kwargs.get("timeout"),
    )


def create_application(
    *,
    testing: bool = False,
    platform_access_provider=None,
    model_invocation_port=None,
    interaction_turn_handler=None,
    dictation_transcription_handler=None,
    dictation_incremental_service=None,
) -> Flask:
    settings = Settings.for_testing() if testing else Settings()
    logger = configure_logging(settings.service_name, settings.log_level)

    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.config["DEBUG"] = False if testing else settings.debug
    app.config["SERVICE_NAME"] = settings.service_name
    app.config["SERVICE_VERSION"] = settings.service_version
    app.config["DELIA_ENV"] = settings.environment
    app.config["PROPAGATE_EXCEPTIONS"] = False

    if platform_access_provider is not None:
        provider = platform_access_provider
    elif settings.core_api_url:
        provider = CorePlatformAccessAdapter(
            core_api_url=settings.core_api_url,
            timeout_seconds=settings.core_timeout_seconds,
            http_get=_bounded_http_get,
        )
    else:
        # Fail-closed for protected routes: middleware returns 503 when unset.
        provider = None

    app.config["PLATFORM_ACCESS_PROVIDER"] = provider

    # C3-MCP-INTEROP-01: provider-neutral specialist boundary. The adapter
    # performs no I/O at composition; unconfigured/disabled specialists and
    # absent user-delegated credentials fail closed at call time.
    # Built before the interaction handler so the bounded C4 governed
    # read can compose on top of it (config-gated, bounded to this task).
    connections = specialist_connections_from_settings(settings)
    # C4-MCP-GOVERNED-READS-01/02: per-binding enabled set — each
    # bounded flag contributes exactly its own authorized tuple at
    # both enforcement boundaries.
    adapter = McpSpecialistAdapter(
        connections,
        credential_provider=_wire_delegated_credential_provider(
            settings, connections
        ),
    )
    # Doc 216: SNAPSHOT_EXPERIMENT (eval-only) routes catalog
    # discovery through the persisted snapshot; invoke stays live.
    # Missing/invalid config fails closed — never silent fallback.
    if settings.mcp_catalog_mode == "snapshot_experiment":
        if not settings.mcp_catalog_db:
            raise RuntimeError(
                "DELIA_MCP_CATALOG_MODE=snapshot_experiment requires "
                "DELIA_MCP_CATALOG_DB"
            )
        from app.application.specialist_interop.snapshot_interop import (
            SnapshotDiscoverInterop,
        )
        from app.infrastructure.interoperability.mcp.catalog_store import (
            McpCatalogStore,
        )

        interop = SnapshotDiscoverInterop(
            adapter, McpCatalogStore(settings.mcp_catalog_db)
        )
    elif settings.mcp_catalog_mode != "live":
        raise RuntimeError(
            "DELIA_MCP_CATALOG_MODE must be 'live' or "
            f"'snapshot_experiment', got {settings.mcp_catalog_mode!r}"
        )
    else:
        interop = SpecialistInterop(adapter)
    app.config["SPECIALIST_INTEROP"] = interop

    # C3-INTERACTION-RUNTIME-01R2: TEST_ONLY deterministic adapter is
    # wired only for testing or explicit injection — never an implicit
    # runtime fallback. Normal runtime wires the approved real provider
    # only when the DELIA_LLM_* configuration is complete; otherwise the
    # handler stays absent and the route fails closed with
    # model_unavailable. InvokeModel still enforces the provider
    # exposure policy at the use-case boundary.
    if interaction_turn_handler is not None:
        handler = interaction_turn_handler
    elif model_invocation_port is not None:
        invoke = InvokeModel(model_invocation_port)
        handler = _compose_turn_handler(
            invoke, DEFAULT_INTERACTION_MODEL_REF, interop, settings,
            connections,
        )
    elif testing:
        invoke = InvokeModel(DeterministicTestAdapter())
        handler = _compose_turn_handler(
            invoke, DEFAULT_INTERACTION_MODEL_REF, interop, settings,
            connections,
        )
    else:
        handler = _wire_real_provider_handler(
            settings, interop, connections
        )
    app.config["INTERACTION_TURN_HANDLER"] = handler

    # VD-F03 dictation.transcription.v1 — same fail-closed pattern as the
    # interaction handler: the real adapter is wired only when DELIA_STT_*
    # is complete; otherwise the capability is absent and the route
    # answers 503 transcription_unavailable. No implicit fallback.
    if dictation_transcription_handler is not None:
        dictation_handler = dictation_transcription_handler
    else:
        dictation_handler = _wire_dictation_handler(settings)
    app.config["DICTATION_TRANSCRIPTION_HANDLER"] = dictation_handler
    app.config["DICTATION_LIMITS"] = {
        "max_audio_bytes": settings.stt_max_audio_bytes,
        "max_duration_ms": settings.stt_max_duration_ms,
    }
    # VD-F06 dictation.incremental.v1 — same fail-closed wiring, plus the
    # explicit admission flag: incremental stays absent until both the
    # STT config is complete AND DELIA_STT_INCREMENTAL_ENABLED=1.
    app.config["DICTATION_INCREMENTAL_SERVICE"] = (
        dictation_incremental_service
        if dictation_incremental_service is not None
        else _wire_incremental_dictation_service(settings)
    )
    app.config["DICTATION_INCREMENTAL_LIMITS"] = {
        "max_session_ms": settings.stt_incremental_max_session_ms,
        "max_segments": settings.stt_incremental_max_segments,
        "max_segment_duration_ms": settings.stt_incremental_max_segment_ms,
        "max_segment_bytes": settings.stt_incremental_max_segment_bytes,
    }

    register_error_handlers(app)
    register_request_logging(app, logger)
    register_auth_middleware(app, logger=logger)
    app.register_blueprint(health_bp)
    register_interaction_routes(app, logger)
    register_dictation_routes(app, logger)

    logger.info(
        "delia_api_started service=%s version=%s env=%s",
        settings.service_name,
        settings.service_version,
        settings.environment,
    )
    return app


def _wire_delegated_credential_provider(settings: Settings, connections):
    """Wire the single-requester token exchange only from complete config.

    C3-MCP-INTEROP-01R1A: without a configured requester client the
    adapter fails closed at call time — no implicit fallback, no
    static-token path.
    """
    if not (
        settings.exchange_token_url
        and settings.exchange_client_id
        and settings.exchange_client_secret
    ):
        return None
    from delpi_auth.jwt_validator import validate_token

    return KeycloakDelegatedCredentialProvider(
        token_url=settings.exchange_token_url,
        client_id=settings.exchange_client_id,
        client_secret=settings.exchange_client_secret,
        timeout_seconds=settings.exchange_timeout_seconds,
        http_post=deadline_http_post,
        subject_bearer_getter=current_subject_bearer,
        token_validator=validate_token,
        cache=InMemoryDelegatedTokenCache(
            max_ttl_seconds=settings.delegated_token_ttl_seconds
        ),
        known_resource_audiences=frozenset(
            profile.resource_audience for profile in connections.values()
        ),
        host_header=settings.exchange_host_header,
    )


def _compose_turn_handler(
    invoke_model: InvokeModel,
    model_ref: ModelRef,
    interop: SpecialistInterop,
    settings: Settings,
    connections,
) -> HandleInteractiveConversationTurn:
    """Compose the turn handler with the specialist-owned live read.

    ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02: capability availability is
    specialist-owned via live tools/list — the read composes over the
    enabled+configured connections with no per-capability flag or
    static binding. The model may propose a selection (never
    authority); deterministic validation + the owner class gate at both
    interop boundaries decide.
    """
    # ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (§6.130):
    # DÉLIA is the OPERATIONAL_CAPABILITY_ORCHESTRATOR over
    # provider-neutral capability groups. MCP is the wired provider
    # family — the approved specialist connections project through
    # McpCapabilityProvider. DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-01:
    # the direct DELPI OpenAPI source is removed — DELPI domain data
    # reaches DÉLIA exclusively through DAVI/MCP; capabilities DAVI
    # does not expose are legitimately unavailable, never served by a
    # direct binding. Live provider surfaces are the capability
    # authority; no per-capability flag or static binding exists.
    # Write-class selections route through the generic governed-write
    # chain with bounded in-memory pending state.
    enabled_specialists = tuple(
        specialist_id
        for specialist_id, profile in connections.items()
        if profile.enabled and profile.endpoint
    )
    providers = []
    if enabled_specialists:
        providers.append(
            McpCapabilityProvider(interop, enabled_specialists)
        )
    # The presentation vocabulary is loaded unconditionally: its
    # ``field_labels`` govern baseline field-name presentation in
    # every path. A missing or invalid resource degrades to neutral
    # fallback labels — fail-closed, never partial.
    vocabulary = None
    try:
        vocabulary = load_cri_presentation_vocabulary(
            _CRI_PRESENTATION_PATH
        )
    except Exception:
        _logger.warning(
            "delia_presentation_vocabulary decision=fail_closed "
            "reason=resource_invalid"
        )
    else:
        field_labels = vocabulary.field_labels
        _logger.info(
            "cri_presentation_resource id=%s version=%s sha256=%s",
            vocabulary.resource_id,
            vocabulary.version,
            vocabulary.content_hash,
        )
        orchestration_instructions = None
    # Doc 231: engine selection is validated unconditionally — an
    # invalid DELIA_ORCHESTRATION_ENGINE fails startup even when no
    # capability surface is configured; nothing is silently selected.
    if (
        settings.orchestration_engine
        not in _SUPPORTED_ORCHESTRATION_ENGINES
    ):
        raise ValueError(
            "DELIA_ORCHESTRATION_ENGINE unsupported: "
            f"{settings.orchestration_engine!r} — expected one of "
            f"{sorted(_SUPPORTED_ORCHESTRATION_ENGINES)}"
        )
    gates = (
        OperationalCapabilityOrchestrator(
            providers,
            invoke_model=invoke_model,
            model_ref=model_ref,
            turn_budget_seconds=settings.turn_budget_seconds,
            model_stage_timeout_seconds=settings.model_stage_timeout_seconds,
            interaction_total_budget_seconds=(
                settings.interaction_total_budget_seconds
            ),
            max_governed_attempts=settings.max_governed_attempts,
            llm_call_max_attempts=settings.llm_call_max_attempts,
            field_labels=field_labels,
            orchestration_instructions=orchestration_instructions,
        )
        if providers and orchestration_instructions is not None
        else None
    )
    investigation_model = None
    investigation_model_factory = None
    if (
        gates is not None
        and settings.orchestration_engine == "pydantic_ai"
    ):
        # Model construction stays inside the infrastructure adapter
        # module so composition never imports pydantic_ai SDK.
        # A new client per turn avoids asyncio locks reused across loops.
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            build_openai_compatible_investigation_model,
        )

        def _investigation_model_factory():
            return build_openai_compatible_investigation_model(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_model,
            )

        investigation_model_factory = _investigation_model_factory
        investigation_model = _investigation_model_factory()
    elif gates is not None and settings.environment == "testing":
        # Unit composition must not require live LLM credentials —
        # the governed gates are exercised through the same production
        # engine with a framework test model (doc 241).
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            build_test_investigation_model,
        )

        investigation_model = build_test_investigation_model()
    orchestration = (
        _resolve_orchestration_attempt(
            settings.orchestration_engine,
            gates,
            investigation_model=investigation_model,
            investigation_model_factory=investigation_model_factory,
            subobjective_fanout_enabled=(
                settings.subobjective_fanout_enabled
            ),
            checkpoint_db_path=settings.checkpoint_db_path,
            **_investigation_runtime_kwargs(settings),
        )
        if gates is not None
        else None
    )
    _logger.info(
        "delia_orchestration_engine selected=%s "
        "surface=%s runtime_sha=%s%s%s",
        settings.orchestration_engine,
        "configured" if orchestration is not None else "absent",
        settings.runtime_sha,
        (
            f" model_id={settings.llm_model}"
            if settings.observability_record_model_id
            else ""
        ),
        (
            " config_profile=%s config_fingerprint=%s"
            % (
                settings.runtime_profile,
                settings.runtime_config_fingerprint,
            )
            if settings.observability_record_config_fingerprint
            else "",
        ),
    )
    return HandleInteractiveConversationTurn(
        invoke_model,
        model_ref=model_ref,
        capability_orchestration=orchestration,
        turn_budget_seconds=settings.turn_budget_seconds,
        timeout_seconds=settings.interaction_call_timeout_seconds,
        llm_call_max_attempts=settings.llm_call_max_attempts,
    )


def _wire_dictation_handler(settings: Settings):
    """Wire the dictation transcription handler only from complete config.

    VD-F03: provider=openai_compatible_audio + base URL + model + key all
    present is the only path that activates the capability — a dedicated
    audio-capable model, never the interaction model, and only through
    the approved OpenAI-compatible provider family. Anything else fails
    closed to `transcription_unavailable`.
    """
    if not (
        settings.stt_provider == "openai_compatible_audio"
        and settings.stt_base_url
        and settings.stt_model
        and settings.stt_api_key
    ):
        return None
    from app.application.dictation.transcribe_dictation import (
        TranscribeDictation,
    )
    from app.infrastructure.model_invocation.openai_compatible_transcription_adapter import (
        OpenAICompatibleTranscriptionAdapter,
    )

    return TranscribeDictation(
        port=OpenAICompatibleTranscriptionAdapter(
            base_url=settings.stt_base_url,
            api_key=settings.stt_api_key,
            model=settings.stt_model,
            timeout_seconds=settings.stt_timeout_seconds,
        ),
        max_audio_bytes=settings.stt_max_audio_bytes,
        max_duration_ms=settings.stt_max_duration_ms,
        rate_limit_per_minute=settings.stt_rate_limit_per_minute,
    )


def _wire_incremental_dictation_service(settings: Settings):
    """Wire dictation.incremental.v1 only from complete config + flag.

    Two gates, both fail-closed: the same complete DELIA_STT_* config as
    the batch path AND the explicit DELIA_STT_INCREMENTAL_ENABLED=1
    admission flag (deploy ships the code with the flag OFF; activation
    is the deliberate post-deploy gate, never implicit).
    """
    if not (
        settings.stt_incremental_enabled
        and settings.stt_provider == "openai_compatible_audio"
        and settings.stt_base_url
        and settings.stt_model
        and settings.stt_api_key
    ):
        return None
    from app.application.dictation.incremental_dictation_session import (
        IncrementalDictationService,
    )
    from app.infrastructure.model_invocation.openai_compatible_transcription_adapter import (
        OpenAICompatibleTranscriptionAdapter,
    )

    return IncrementalDictationService(
        port=OpenAICompatibleTranscriptionAdapter(
            base_url=settings.stt_base_url,
            api_key=settings.stt_api_key,
            model=settings.stt_model,
            timeout_seconds=settings.stt_timeout_seconds,
        ),
        max_session_ms=settings.stt_incremental_max_session_ms,
        max_segments=settings.stt_incremental_max_segments,
        max_segment_duration_ms=settings.stt_incremental_max_segment_ms,
        max_segment_bytes=settings.stt_incremental_max_segment_bytes,
        max_total_bytes=settings.stt_max_audio_bytes,
        session_ttl_ms=settings.stt_incremental_max_session_ms + 60_000,
        rate_limit_per_minute=settings.stt_rate_limit_per_minute,
        max_in_flight=settings.stt_incremental_max_in_flight,
    )


def _wire_real_provider_handler(settings: Settings, interop, connections):
    """Wire the real OpenAI-compatible provider only from complete config.

    provider=openai_compatible + base URL + model + key all present is the
    only path that activates a real adapter. Anything else stays absent
    and the route fails closed — no implicit TEST_ONLY fallback.
    """
    if settings.llm_egress_blocked_reason:
        _logger.warning(
            "delia real provider not wired: %s", settings.llm_egress_blocked_reason
        )
        return None
    if not (
        settings.llm_provider == "openai_compatible"
        and settings.llm_base_url
        and settings.llm_model
        and settings.llm_api_key
    ):
        return None
    # Doc 243: Pydantic AI is the only model invocation runtime — the
    # retired alternate adapter branch and the DELIA_MODEL_RUNTIME
    # selector are removed; stale env values fail closed in Settings.
    from app.infrastructure.model_invocation.pydantic_ai_adapter import (
        PydanticAiModelInvocationAdapter,
    )

    adapter = PydanticAiModelInvocationAdapter(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        default_max_output_units=settings.llm_max_output_tokens,
        context_window_tokens=settings.llm_context_tokens,
    )
    model_ref = ModelRef(
        model_id=settings.llm_model,
        version="configured",
        owner_ref="DELPI",
        provider_ref="openai_compatible",
    )
    return _compose_turn_handler(
        InvokeModel(adapter), model_ref, interop, settings, connections
    )
