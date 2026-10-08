from __future__ import annotations

from flask import Flask

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
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
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.health_routes import health_bp
from app.interfaces.http.interaction_routes import register_interaction_routes
from app.interfaces.http.request_logging import register_request_logging


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

    register_error_handlers(app)
    register_request_logging(app, logger)
    register_auth_middleware(app, logger=logger)
    app.register_blueprint(health_bp)
    register_interaction_routes(app, logger)

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
    orchestration = (
        OperationalCapabilityOrchestrator(
            providers,
            invoke_model=invoke_model,
            model_ref=model_ref,
            turn_budget_seconds=settings.turn_budget_seconds,
            model_stage_timeout_seconds=settings.model_stage_timeout_seconds,
        )
        if providers
        else None
    )
    return HandleInteractiveConversationTurn(
        invoke_model,
        model_ref=model_ref,
        capability_orchestration=orchestration,
        turn_budget_seconds=settings.turn_budget_seconds,
    )


def _wire_real_provider_handler(settings: Settings, interop, connections):
    """Wire the real OpenAI-compatible provider only from complete config.

    provider=openai_compatible + base URL + model + key all present is the
    only path that activates a real adapter. Anything else stays absent
    and the route fails closed — no implicit TEST_ONLY fallback.
    """
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
