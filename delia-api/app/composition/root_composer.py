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
from app.application.capability_provision.openapi_provider import (
    OpenApiCapabilityProvider,
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
    load_cri_instruction_clause,
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
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.dictation_routes import register_dictation_routes
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.health_routes import health_bp
from app.interfaces.http.interaction_routes import register_interaction_routes
from app.interfaces.http.request_logging import register_request_logging

_logger = logging.getLogger(__name__)

# CRI E2-R3/E3: governed declarative resources — fixed repo
# artifacts, never request/env-supplied paths.
_CRI_INSTRUCTIONS_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "cri_instructions.delpi.json"
)
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
    interop = SpecialistInterop(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        ),
    )
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


def _wire_openapi_provider(settings: Settings):
    """Compose the OpenAPI provider family — absent unless configured.

    ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (§6.130): the
    DELPI OpenAPI source activates only with base URL + governed
    declarations file; anything missing fails closed to no source.
    """
    if not (
        settings.openapi_delpi_enabled
        and settings.openapi_delpi_base_url
        and settings.openapi_delpi_declarations_path
    ):
        return None
    from app.infrastructure.openapi.source_loader import (
        build_openapi_source,
    )

    source = build_openapi_source(
        source_id="delpi",
        base_url=settings.openapi_delpi_base_url,
        declarations_path=settings.openapi_delpi_declarations_path,
        http_get=deadline_http_get,
        subject_bearer_getter=current_subject_bearer,
        timeout_seconds=settings.openapi_timeout_seconds,
    )
    if source is None:
        return None
    return OpenApiCapabilityProvider([source])


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
    # provider-neutral capability groups. MCP is one provider family —
    # the approved specialist connections project through
    # McpCapabilityProvider; OpenAPI sources project through
    # OpenApiCapabilityProvider when configured. Live provider surfaces
    # are the capability authority; no per-capability flag or static
    # binding exists. Write-class selections route through the generic
    # governed-write chain with bounded in-memory pending state.
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
    openapi_provider = _wire_openapi_provider(settings)
    if openapi_provider is not None:
        providers.append(openapi_provider)
    # CRI E2-R3/E3-G1: the declarative resources are loaded and
    # validated only when the mode is REQUESTED. The *effective* mode
    # is the single resolved truth propagated to both the handler
    # (observability) and the orchestrator (behavior): requested ON
    # with any absent/invalid resource resolves to baseline — CRI is
    # never logged as executed when the fallback deactivated it.
    cri_clause = None
    cri_version = None
    cri_vocabulary = None
    field_labels = None
    cri_requested = bool(settings.response_intelligence_enabled)
    # The presentation vocabulary is loaded unconditionally: its
    # ``field_labels`` govern baseline field-name presentation in
    # every path, independent of the CRI activation flag. A missing
    # or invalid resource degrades to neutral fallback labels; when
    # CRI was requested it also disables the composed response —
    # fail-closed, never partial.
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
    if cri_requested:
        try:
            clause = load_cri_instruction_clause(_CRI_INSTRUCTIONS_PATH)
        except Exception:
            _logger.warning(
                "delia_response_intelligence decision=fail_closed "
                "reason=cri_resource_invalid"
            )
        else:
            if vocabulary is None:
                _logger.warning(
                    "delia_response_intelligence decision=fail_closed "
                    "reason=cri_resource_invalid"
                )
            else:
                cri_clause = clause.text
                cri_version = clause.version
                cri_vocabulary = vocabulary.sections
                _logger.info(
                    "cri_instruction_resource id=%s version=%s "
                    "sha256=%s",
                    clause.resource_id,
                    clause.version,
                    clause.content_hash,
                )
    try:
        orchestration_instructions = load_orchestration_instructions(
            _ORCHESTRATION_INSTRUCTIONS_PATH,
            required_names=ORCHESTRATION_INSTRUCTION_KEYS,
        ).instructions
    except Exception:
        _logger.warning(
            "delia_orchestration_instructions decision=fail_closed "
            "reason=resource_invalid"
        )
        orchestration_instructions = None
    cri_effective = cri_requested and cri_vocabulary is not None
    orchestration = (
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
            response_intelligence_enabled=cri_effective,
            cri_instruction_clause=cri_clause,
            cri_instruction_version=cri_version,
            cri_presentation_vocabulary=cri_vocabulary,
            field_labels=field_labels,
            orchestration_instructions=orchestration_instructions,
        )
        if providers and orchestration_instructions is not None
        else None
    )
    # CRI E1 (doc 73 §7 / spec 75 §4.1): the single response-intelligence
    # decision is resolved here from trusted runtime config — never from
    # request, model, provider or frontend state. Invalid env values
    # fail closed to baseline; the switch selects only the governed
    # outcome → response boundary mode, it authorizes nothing.
    _logger.info(
        "delia_response_intelligence requested=%s effective=%s "
        "config_source=%s runtime_sha=%s",
        "cri" if cri_requested else "baseline",
        "cri" if cri_effective else "baseline",
        settings.response_intelligence_config_source,
        settings.runtime_sha,
    )
    if settings.response_intelligence_config_invalid:
        _logger.warning(
            "delia_response_intelligence decision=fail_closed "
            "reason=invalid_env_value"
        )
    # Doc 103 GATE 1: per-logical-call LLM retry limit — an invalid
    # env value resolves to 1 (OFF), never to retries on.
    if settings.llm_call_max_attempts_config_invalid:
        _logger.warning(
            "delia_llm_call_max_attempts decision=fail_closed "
            "reason=invalid_env_value"
        )
    return HandleInteractiveConversationTurn(
        invoke_model,
        model_ref=model_ref,
        capability_orchestration=orchestration,
        turn_budget_seconds=settings.turn_budget_seconds,
        llm_call_max_attempts=settings.llm_call_max_attempts,
        response_intelligence_enabled=cri_effective,
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
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        default_max_output_units=settings.llm_max_output_tokens,
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
