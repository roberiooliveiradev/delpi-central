"""Application-facing port for provider-neutral model invocation.

49 lists ModelInferencePort as a possible future port. C3-T3 realizes one
invocation port under this name. Do not add a second parallel port.
"""

from __future__ import annotations

from typing import Protocol

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.domain.model_invocation.model import ProviderExposureClass


class ModelInvocationPort(Protocol):
    """Semantic invocation needs only. No vendor SDK types."""

    @property
    def adapter_kind(self) -> str:
        """TEST_ONLY or a future approved provider kind. Never a production default."""

    @property
    def exposure_class(self) -> ProviderExposureClass:
        """TEST_ONLY until the real-provider gate is fully PROVEN for DÉLIA."""

    @property
    def context_window_tokens(self) -> int | None:
        """Declared effective input window in tokens — the runtime value
        actually honored by the provider, not the model's nominal capacity.

        None means the window is unknown: the application boundary then
        applies no pre-call budget enforcement. Configuration is owned by
        infrastructure; the value is provider-neutral (tokens only)."""
        return None

    @property
    def default_max_output_units(self) -> int | None:
        """Adapter-configured default generation cap — the limit actually
        requested from the provider when the invocation request does not
        set ``generation_config.max_output_units``.

        The pre-call budget must reserve exactly what will be sent;
        resolving the reserve anywhere else would diverge from the wire.
        None means the adapter has no default: the budget then applies
        the documented floor reserve."""
        return None

    def invoke(self, request: ModelInvocationRequest) -> ProviderInvocationPayload:
        """Execute one bounded invocation.

        Must honor request.timeout_seconds. Must not execute tools, ACT, or writes.
        Must raise ModelInvocationError with a semantic code — never a raw SDK exception.
        """
