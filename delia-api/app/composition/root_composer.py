from __future__ import annotations

import requests
from flask import Flask

from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import ModelRef
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
            http_get=requests.get,
        )
    else:
        # Fail-closed for protected routes: middleware returns 503 when unset.
        provider = None

    app.config["PLATFORM_ACCESS_PROVIDER"] = provider

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
        handler = HandleInteractiveConversationTurn(
            InvokeModel(model_invocation_port)
        )
    elif testing:
        handler = HandleInteractiveConversationTurn(
            InvokeModel(DeterministicTestAdapter())
        )
    else:
        handler = _wire_real_provider_handler(settings)
    app.config["INTERACTION_TURN_HANDLER"] = handler

    # C3-MCP-INTEROP-01: provider-neutral specialist boundary. The adapter
    # performs no I/O at composition; unconfigured/disabled specialists and
    # absent user-delegated credentials fail closed at call time.
    connections = specialist_connections_from_settings(settings)
    app.config["SPECIALIST_INTEROP"] = SpecialistInterop(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )

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
        http_post=requests.post,
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


def _wire_real_provider_handler(settings: Settings):
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
    )
    return HandleInteractiveConversationTurn(
        InvokeModel(adapter),
        model_ref=ModelRef(
            model_id=settings.llm_model,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
    )
