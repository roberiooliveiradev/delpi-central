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

    def invoke(self, request: ModelInvocationRequest) -> ProviderInvocationPayload:
        """Execute one bounded invocation.

        Must honor request.timeout_seconds. Must not execute tools, ACT, or writes.
        Must raise ModelInvocationError with a semantic code — never a raw SDK exception.
        """
