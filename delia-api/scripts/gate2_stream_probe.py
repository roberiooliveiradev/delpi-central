"""DELIA-C3 GATE 2 — real-socket NDJSON stream probe (dev-local only).

Serves the REAL ``POST /interaction/turns`` WSGI app on a throwaway
port with a shortened keepalive interval, so transport behavior
(keepalive bytes on the wire, disconnect -> cancel_check, single
terminal) is provable over a real TCP/HTTP connection without waiting
wall-clock minutes.

Two probe handlers, selected by ``PROBE_MODE``:

- ``silent``: real ``HandleInteractiveConversationTurn`` whose model
  adapter sleeps ``PROBE_SILENT_SECONDS`` then answers — keepalives
  must flow while the turn is live; the single terminal arrives after.
- ``flaky``: the adapter raises a recoverable TIMEOUT twice, then
  answers — under ``DELIA_LLM_CALL_MAX_ATTEMPTS=3`` two real retries
  run and CONTINUING events flow; under the fail-closed default the
  single invocation terminates honestly.

The platform-access provider is a test double accepting any bearer —
it proves transport + settings wiring, NOT authorization (covered by
the deterministic suite and real-Keycloak tests).

Never run in production; never points at external LLM endpoints.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.interfaces.http.interaction_routes as routes
from app.application.interaction.activity import ActivityPhase
from app.application.interaction.contracts import InteractiveTurnResult
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app
from app.domain.model_invocation.model import ProviderExposureClass
from app.infrastructure.config.settings import Settings

routes._INTERACTION_KEEPALIVE_SECONDS = float(
    os.getenv("PROBE_KEEPALIVE_SECONDS", "0.5")
)


class _ProbeProvider:
    """Any bearer resolves to a bounded test context — transport probe
    only, never an authorization surface."""

    def resolve(self, bearer_token: str):
        return PlatformAccessContext(
            user_id="probe-user",
            name="Probe",
            email="probe@local",
            effective_permissions=("delia.access",),
        )


class _SilentAdapter:
    ADAPTER_KIND = "TEST_ONLY"
    EXPOSURE_CLASS = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.calls = 0

    @property
    def adapter_kind(self):
        return self.ADAPTER_KIND

    @property
    def exposure_class(self):
        return self.EXPOSURE_CLASS

    def invoke(self, request):
        self.calls += 1
        time.sleep(float(os.getenv("PROBE_SILENT_SECONDS", "2.0")))
        return ProviderInvocationPayload(
            structured_output={
                "answer": "probe ok",
                "limitations": [],
            },
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _FlakyAdapter(_SilentAdapter):
    def invoke(self, request):
        self.calls += 1
        if self.calls <= 2:
            raise ModelInvocationError(TIMEOUT, "probe timeout")
        return super().invoke(request)


class _AlwaysTimeoutAdapter(_SilentAdapter):
    def invoke(self, request):
        self.calls += 1
        time.sleep(float(os.getenv("PROBE_SILENT_SECONDS", "2.0")))
        raise ModelInvocationError(TIMEOUT, "probe timeout")


_ADAPTERS = {
    "silent": _SilentAdapter,
    "flaky": _FlakyAdapter,
    "always_timeout": _AlwaysTimeoutAdapter,
}


def _build() -> tuple:
    settings = Settings()
    adapter = _ADAPTERS[os.getenv("PROBE_MODE", "silent")]()
    handler = HandleInteractiveConversationTurn(
        InvokeModel(adapter),
        turn_budget_seconds=settings.turn_budget_seconds,
        llm_call_max_attempts=settings.llm_call_max_attempts,
    )
    return settings, adapter, handler


def main() -> int:
    settings, adapter, handler = _build()
    app = create_app(
        testing=True,
        platform_access_provider=_ProbeProvider(),
        interaction_turn_handler=handler,
    )
    app.add_url_rule(
        "/probe/stats",
        view_func=lambda: {
            "adapter_calls": adapter.calls,
            "llm_call_max_attempts": settings.llm_call_max_attempts,
            "turn_budget_seconds": settings.turn_budget_seconds,
        },
    )
    port = int(os.getenv("PROBE_PORT", "18001"))
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
