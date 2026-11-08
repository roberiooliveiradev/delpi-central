"""Pydantic AI runtime adapter for ModelInvocationPort (M2, doc 220).

Same governed port contract as ``OpenAICompatibleModelInvocationAdapter``
— one bounded structured-output invocation per call, no tools, no ACT,
no provider authority. The orchestrator's gates, validation, deadlines
and output checks stay unchanged: this adapter only replaces the
transport/structured-generation mechanics behind the port.

The per-call ``output_type`` model is built from the request's
``expected_fields`` (extra keys allowed — ``limitations`` and governed
surplus fields pass through exactly as the legacy path tolerates them;
the use case's ``_validate_structured_output`` remains the definitive
contract check).
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Mapping

from pydantic import ConfigDict, create_model

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_REJECTED,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.contracts import UsageMetadata
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ProviderExposureClass,
)

_logger = logging.getLogger(__name__)

def _structured_output_directive(request) -> str:
    """Same required-fields enumeration the legacy JSON-mode directive
    sent — the model must see the obligated field names explicitly
    (M6 finding: without it the model omitted required wrappers like
    "arguments" and emitted surplus keys instead)."""
    fields = ", ".join(f'"{name}"' for name in request.expected_fields)
    return (
        "Respond ONLY with a single JSON object matching the declared "
        f"fields. Required fields: {fields}. Use JSON types that match "
        "each field (string, number, boolean, object, or array). "
        'You MAY include "limitations": an array of short strings '
        "describing what could not be verified — omit it when the "
        "required fields alone answer the schema."
    )


def _proposal_model(expected_fields: tuple[str, ...] | list[str]):
    """Dynamic output model — declared fields REQUIRED at the wire
    (the governed contract lists them as required), extras allowed
    for governed surplus keys like "limitations". Companion fields of
    an "applicable" proposal stay optional so abstention
    (applicable=false without companion ids) remains legal."""
    declared = [
        name
        for name in expected_fields
        if isinstance(name, str) and name
    ]
    abstains = "applicable" in declared
    fields = {}
    for name in declared:
        if abstains and name != "applicable":
            fields[name] = (Any | None, None)
        else:
            fields[name] = (Any | None, ...)
    return create_model(
        "StageProposal", __config__=ConfigDict(extra="allow"), **fields
    )


class PydanticAiModelInvocationAdapter:
    """``pydantic_ai.Agent`` behind ModelInvocationPort — M2 runtime.

    Constructor contract mirrors the legacy adapter so composition can
    select either implementation behind the same ``InvokeModel``
    boundary — never both in one request.
    """

    ADAPTER_KIND = "OPENAI_COMPATIBLE"
    EXPOSURE_CLASS = ProviderExposureClass.EXTERNAL_APPROVED

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        default_max_output_units: int | None = None,
        context_window_tokens: int | None = None,
        model_impl: Any | None = None,
    ) -> None:
        for name, value in (
            ("base_url", base_url),
            ("api_key", api_key),
            ("model", model),
        ):
            if not str(value or "").strip():
                raise ValueError(f"provider configuration missing {name}")
        if timeout_seconds <= 0:
            raise ValueError("provider timeout_seconds must be > 0")
        self._model_name = model
        self._timeout_seconds = timeout_seconds
        self._default_max_output_units = (
            default_max_output_units
            if isinstance(default_max_output_units, int)
            and not isinstance(default_max_output_units, bool)
            and default_max_output_units > 0
            else None
        )
        self._context_window_tokens = (
            context_window_tokens
            if isinstance(context_window_tokens, int)
            and not isinstance(context_window_tokens, bool)
            and context_window_tokens > 0
            else None
        )
        if model_impl is not None:
            # Test/injected model — composition of the Agent still
            # happens per invoke with the declared output model.
            self._model_impl = model_impl
        else:
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.openai import OpenAIProvider

            self._model_impl = OpenAIChatModel(
                model,
                provider=OpenAIProvider(
                    base_url=base_url.rstrip("/"), api_key=api_key
                ),
            )

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    @property
    def exposure_class(self) -> ProviderExposureClass:
        return self.EXPOSURE_CLASS

    @property
    def context_window_tokens(self) -> int | None:
        return self._context_window_tokens

    @property
    def default_max_output_units(self) -> int | None:
        return self._default_max_output_units

    def invoke(
        self, request: ModelInvocationRequest
    ) -> ProviderInvocationPayload:
        from pydantic_ai.output import PromptedOutput
from pydantic_ai import Agent
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            TextPart,
            UserPromptPart,
        )
        from pydantic_ai.settings import ModelSettings

        timeout = min(
            float(request.timeout_seconds), float(self._timeout_seconds)
        )
        started = time.monotonic()
        # ``instructions=`` (not ``system_prompt=``): with a nonempty
        # ``message_history`` pydantic-ai does NOT emit a
        # SystemPromptPart, silently dropping the current stage
        # instruction — observed invalid_structured_output churn on
        # multi-turn requests. ``instructions`` is set on the new
        # ModelRequest regardless of history (verified on wire,
        # pydantic-ai 2.50.0).
        stage_instructions = (
            (request.instruction_content or "").strip()
            + "\n\n"
            + _structured_output_directive(request)
        ).strip()
        agent = Agent(
            self._model_impl,
            output_type=PromptedOutput(_proposal_model(tuple(request.expected_fields))),
            instructions=stage_instructions,
        )
        history: list[Any] = []
        for turn in request.prior_context:
            if turn.kind is TurnKind.USER_INPUT:
                history.append(
                    ModelRequest(parts=[UserPromptPart(turn.content)])
                )
            else:
                history.append(
                    ModelResponse(parts=[TextPart(turn.content)])
                )
        max_output_units = (
            request.generation_config.max_output_units
            or self._default_max_output_units
        )
        settings = ModelSettings(timeout=timeout)
        if max_output_units:
            settings["max_tokens"] = int(max_output_units)
        try:
            # httpx/OpenAI per-read timeouts reset on every trickle
            # chunk — ModelSettings.timeout alone cannot bound a
            # never-finishing body. Enforce the absolute wall-clock
            # deadline here (parity with the retired requests adapter).
            # Daemon worker: after TIMEOUT the caller returns without
            # joining a still-trickling HTTP read (non-daemon pools
            # keep the interpreter alive and hang pytest teardown).
            box: dict[str, Any] = {}

            def _run_agent() -> None:
                try:
                    box["result"] = agent.run_sync(
                        request.input_text,
                        message_history=history or None,
                        model_settings=settings,
                    )
                except BaseException as exc:  # noqa: BLE001 — re-raise below
                    box["error"] = exc

            worker = threading.Thread(
                target=_run_agent, name="delia-model-invoke", daemon=True
            )
            worker.start()
            worker.join(timeout=timeout)
            if worker.is_alive():
                raise ModelInvocationError(
                    TIMEOUT,
                    "provider request exceeded its wall-clock deadline",
                )
            if "error" in box:
                raise box["error"]
            result = box["result"]
        except ModelInvocationError:
            raise
        except Exception as exc:
            raise self._map_error(exc, started) from exc
        duration_ms = int((time.monotonic() - started) * 1000)
        output = getattr(result, "output", None)
        if output is None:
            output = getattr(result, "data", None)
        if output is None:
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "provider returned no structured output",
            )
        structured = (
            # exclude_unset: an omitted optional field must surface as
            # an ABSENT key — exactly like the legacy JSON-mode path —
            # so the governed presence check can distinguish "model
            # returned null" from "model never emitted the field".
            output.model_dump(exclude_unset=True)
            if hasattr(output, "model_dump")
            else dict(output)
            if isinstance(output, Mapping)
            else None
        )
        if not isinstance(structured, dict):
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "provider output is not an object",
            )
        return ProviderInvocationPayload(
            structured_output=structured,
            generated_at=datetime.now(timezone.utc).isoformat(),
            finish_status=InvocationFinishStatus.COMPLETED,
            usage=self._map_usage(result),
            duration_ms=duration_ms,
        )

    @staticmethod
    def _map_usage(result: Any) -> UsageMetadata | None:
        usage = getattr(result, "usage", None)
        fn = usage if callable(usage) else None
        data = fn() if fn is not None else usage
        if data is None:
            return None
        input_units = getattr(
            data, "input_tokens", None
        ) or getattr(data, "request_tokens", None)
        output_units = getattr(
            data, "output_tokens", None
        ) or getattr(data, "response_tokens", None)
        if input_units is None and output_units is None:
            return None
        return UsageMetadata(
            input_units=(
                int(input_units) if input_units is not None else None
            ),
            output_units=(
                int(output_units) if output_units is not None else None
            ),
        )

    @staticmethod
    def _map_error(exc: Exception, started: float) -> ModelInvocationError:
        name = type(exc).__name__.lower()
        text = str(exc)[:200]
        if time.monotonic() - started > 0 and (
            "timeout" in name or "timed out" in text.lower()
        ):
            return ModelInvocationError(
                TIMEOUT, "provider request timed out"
            )
        if (
            "unexpectedmodelbehavior" in name
            or "valueerror" in name
            or "validation" in name
        ):
            return ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "provider output failed structured validation",
            )
        # pydantic-ai ModelHTTPError and transport errors may carry
        # status_code — map it regardless of the wrapper type.
        status = getattr(exc, "status_code", None)
        if status is not None:
            if status in (401, 403):
                return ModelInvocationError(
                    PROVIDER_REJECTED,
                    "provider rejected request (auth)",
                )
            if status == 404:
                return ModelInvocationError(
                    PROVIDER_REJECTED,
                    "provider reports model or endpoint unsupported",
                )
            if status == 429 or (isinstance(status, int) and status >= 500):
                return ModelInvocationError(
                    PROVIDER_UNAVAILABLE,
                    "provider unavailable",
                )
            return ModelInvocationError(
                PROVIDER_REJECTED, "provider rejected request"
            )
        return ModelInvocationError(
            PROVIDER_UNAVAILABLE, "provider unreachable"
        )
