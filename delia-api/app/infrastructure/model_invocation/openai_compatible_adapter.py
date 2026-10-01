"""OpenAI-compatible Infrastructure adapter for ModelInvocationPort.

C3-INTERACTION-RUNTIME-01R2: first real-provider binding behind the
existing port. Provider-neutral: receives base_url/api_key/model/timeout
from Infrastructure configuration and knows nothing about vendor or
gateway names. Minha DELPI Chat runtime/prompts/providers are not reused.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

import requests

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_REJECTED,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
    UNSUPPORTED_MODEL,
    ModelInvocationError,
)
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ProviderExposureClass,
    UsageMetadata,
)


_PROVIDER_TOOL_FIELDS = ("tool_calls", "function_call", "tool_call", "function_calls")


class OpenAICompatibleModelInvocationAdapter:
    """POST {base_url}/chat/completions behind ModelInvocationPort.

    No tools, no function calling, no streaming. The API key is only used
    for the provider Authorization header and is never returned, logged,
    or embedded in errors.
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
        http_post: Callable[..., Any] = requests.post,
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
        self._endpoint = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._http_post = http_post

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    @property
    def exposure_class(self) -> ProviderExposureClass:
        return self.EXPOSURE_CLASS

    def invoke(self, request: ModelInvocationRequest) -> ProviderInvocationPayload:
        timeout = min(float(request.timeout_seconds), float(self._timeout_seconds))
        started = time.monotonic()
        try:
            response = self._http_post(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=self._request_payload(request),
                timeout=timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise ModelInvocationError(
                TIMEOUT, "provider request timed out"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ModelInvocationError(
                PROVIDER_UNAVAILABLE, "provider unreachable"
            ) from exc
        duration_ms = int((time.monotonic() - started) * 1000)
        self._check_status(response.status_code)
        return self._map_response(response, duration_ms)

    def _request_payload(self, request: ModelInvocationRequest) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if request.instruction_content:
            messages.append(
                {"role": "system", "content": request.instruction_content}
            )
        messages.append(
            {"role": "system", "content": self._structured_output_directive(request)}
        )
        # Prior interaction context is untrusted data, never system policy.
        # DÉLIA turn kinds map deterministically: USER_INPUT -> user,
        # DELIA_RESULT -> assistant. No tools, no authority fields.
        for turn in request.prior_context:
            role = "user" if turn.kind is TurnKind.USER_INPUT else "assistant"
            messages.append({"role": role, "content": turn.content})
        messages.append({"role": "user", "content": request.input_text})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        if request.generation_config.max_output_units:
            payload["max_tokens"] = int(request.generation_config.max_output_units)
        return payload

    @staticmethod
    def _structured_output_directive(request: ModelInvocationRequest) -> str:
        fields = ", ".join(f'"{name}"' for name in request.expected_fields)
        return (
            "Respond ONLY with a single JSON object. No prose, no markdown "
            f"fences. Required fields: {fields}. Each value must be a plain "
            'string. Optionally include "limitations": an array of short '
            "strings describing what the answer could not verify or cover."
        )

    @staticmethod
    def _check_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code in (401, 403):
            raise ModelInvocationError(
                PROVIDER_REJECTED,
                f"provider rejected request (HTTP {status_code})",
            )
        if status_code == 404:
            raise ModelInvocationError(
                UNSUPPORTED_MODEL,
                "provider reports model or endpoint unsupported (HTTP 404)",
            )
        if status_code == 429 or status_code >= 500:
            raise ModelInvocationError(
                PROVIDER_UNAVAILABLE,
                f"provider unavailable (HTTP {status_code})",
            )
        raise ModelInvocationError(
            PROVIDER_REJECTED,
            f"provider rejected request (HTTP {status_code})",
        )

    def _map_response(self, response: Any, duration_ms: int) -> ProviderInvocationPayload:
        try:
            body = response.json()
        except ValueError as exc:
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT, "provider response is not valid JSON"
            ) from exc
        if not isinstance(body, Mapping):
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT, "provider response is not an object"
            )
        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "provider response missing assistant message",
            ) from exc
        if not isinstance(message, Mapping):
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT, "provider message is not an object"
            )
        for field in _PROVIDER_TOOL_FIELDS:
            if message.get(field):
                raise ModelInvocationError(
                    INVALID_STRUCTURED_OUTPUT,
                    f"provider returned forbidden tool field '{field}'",
                )
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT, "provider message content is empty"
            )
        structured = self._parse_structured_output(content)
        return ProviderInvocationPayload(
            structured_output=structured,
            generated_at=datetime.now(timezone.utc).isoformat(),
            finish_status=InvocationFinishStatus.COMPLETED,
            usage=self._map_usage(body.get("usage")),
            duration_ms=duration_ms,
        )

    @staticmethod
    def _parse_structured_output(content: str) -> Mapping[str, Any]:
        text = content.strip()
        parsed: Any = None
        try:
            parsed = json.loads(text)
        except ValueError:
            if text.startswith("```"):
                inner = text.strip("`").removeprefix("json").strip()
                try:
                    parsed = json.loads(inner)
                except ValueError:
                    parsed = None
        if not isinstance(parsed, dict):
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "model output is not a JSON object",
            )
        return parsed

    @staticmethod
    def _map_usage(usage: Any) -> UsageMetadata | None:
        if not isinstance(usage, Mapping):
            return None
        return UsageMetadata(
            input_units=_int_or_none(usage.get("prompt_tokens")),
            output_units=_int_or_none(usage.get("completion_tokens")),
            unit_kind="tokens",
        )


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    return int(value) if isinstance(value, (int, float)) else None
