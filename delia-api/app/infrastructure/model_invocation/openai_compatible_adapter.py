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
from app.infrastructure.http.deadline_transport import (
    deadline_http_post,
    deadline_scope,
)


_PROVIDER_TOOL_FIELDS = ("tool_calls", "function_call", "tool_call", "function_calls")

# LOOP-03R2A: ``timeout_seconds`` is the MAXIMUM WALL-CLOCK DURATION of
# one invocation — not a socket read timeout. ``requests`` applies the
# read timeout per socket recv, so a server that trickles bytes would
# keep the call alive forever. The body is therefore streamed and the
# monotonic deadline re-checked between chunks; the in-flight socket
# timeout is tightened to the remaining budget so a mid-body stall
# cannot outlive the deadline by more than one read slice.
_READ_SLICE_SECONDS = 0.5
_BODY_CHUNK_BYTES = 65536
_MAX_BODY_BYTES = 4 * 1024 * 1024


class OpenAICompatibleModelInvocationAdapter:
    """POST {base_url}/chat/completions behind ModelInvocationPort.

    No tools, no function calling. ``stream=True`` is used internally
    only so the response body can be drained under the total
    wall-clock deadline — the provider contract stays
    request/response JSON, not SSE. The API key is only used for the
    provider Authorization header and is never returned, logged, or
    embedded in errors.
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
        http_post: Callable[..., Any] = deadline_http_post,
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
        deadline = started + timeout
        response = None
        try:
            # LOOP-03R2A-R3: bind the absolute deadline thread-locally so
            # deadline-wrapped transports enforce it during status-line
            # and header parsing too — not only during body drain.
            with deadline_scope(deadline):
                response = self._http_post(
                    self._endpoint,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=self._request_payload(request),
                    # (connect, read): connect is bounded by the whole
                    # remaining invocation budget; the per-recv read
                    # slice bounds how long a single socket read can
                    # stall while the chunked drain enforces the total
                    # deadline.
                    timeout=(
                        timeout,
                        min(timeout, _READ_SLICE_SECONDS),
                    ),
                    stream=True,
                )
            self._check_status(response.status_code)
            body = self._read_body(response, deadline)
        except ModelInvocationError:
            raise
        except requests.exceptions.Timeout as exc:
            raise ModelInvocationError(
                TIMEOUT, "provider request timed out"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ModelInvocationError(
                PROVIDER_UNAVAILABLE, "provider unreachable"
            ) from exc
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
        if time.monotonic() >= deadline:
            raise ModelInvocationError(
                TIMEOUT, "provider request exceeded its wall-clock deadline"
            )
        duration_ms = int((time.monotonic() - started) * 1000)
        return self._map_body(body, duration_ms)

    def _read_body(self, response: Any, deadline: float) -> Any:
        """Drain the response body under the absolute deadline.

        Returns the decoded JSON body. A mid-stream stall or a
        never-completing trickle ends in TIMEOUT, never in a call
        that outlives ``timeout_seconds``.
        """
        if time.monotonic() >= deadline:
            raise ModelInvocationError(
                TIMEOUT, "provider request timed out"
            )
        # ``iter_content`` cannot enforce the deadline: urllib3 fills
        # the whole requested amt per read, so a trickling server
        # keeps one ``read(amt)`` alive past the budget. ``read1``
        # returns after at most one socket recv — the deadline is
        # re-checked between every read and a stall aborts at the
        # tightened per-recv socket timeout.
        raw = getattr(response, "raw", None)
        read1 = getattr(raw, "read1", None)
        iter_content = getattr(response, "iter_content", None)
        if not callable(read1) and not callable(iter_content):
            # Test stubs materialize the body already — the deadline
            # check above still bounds the total duration.
            try:
                return response.json()
            except ValueError as exc:
                raise ModelInvocationError(
                    INVALID_STRUCTURED_OUTPUT,
                    "provider response is not valid JSON",
                ) from exc
        chunks = bytearray()
        if callable(read1):
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ModelInvocationError(
                        TIMEOUT,
                        "provider response exceeded its wall-clock "
                        "deadline",
                    )
                self._tighten_socket_timeout(response, remaining)
                try:
                    chunk = read1(_BODY_CHUNK_BYTES)
                except Exception as exc:
                    # urllib3/http.client mid-body errors surface as
                    # protocol/socket exceptions, not requests'.
                    raise (
                        ModelInvocationError(
                            TIMEOUT,
                            "provider response exceeded its "
                            "wall-clock deadline",
                        )
                        if time.monotonic() >= deadline
                        or isinstance(exc, TimeoutError)
                        else ModelInvocationError(
                            PROVIDER_UNAVAILABLE,
                            "provider response failed mid-body",
                        )
                    ) from exc
                if not chunk:
                    break
                chunks += chunk
                if len(chunks) > _MAX_BODY_BYTES:
                    raise ModelInvocationError(
                        PROVIDER_REJECTED,
                        "provider response exceeds the size limit",
                    )
        else:
            for chunk in iter_content(chunk_size=_BODY_CHUNK_BYTES):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ModelInvocationError(
                        TIMEOUT,
                        "provider response exceeded its wall-clock "
                        "deadline",
                    )
                self._tighten_socket_timeout(response, remaining)
                if chunk:
                    chunks += chunk
                    if len(chunks) > _MAX_BODY_BYTES:
                        raise ModelInvocationError(
                            PROVIDER_REJECTED,
                            "provider response exceeds the size limit",
                        )
        try:
            return json.loads(bytes(chunks))
        except ValueError as exc:
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "provider response is not valid JSON",
            ) from exc

    @staticmethod
    def _tighten_socket_timeout(response: Any, remaining: float) -> None:
        """Best-effort shrink of the in-flight socket timeout.

        With ``stream=True`` the per-recv timeout was fixed at request
        time; tightening it to the remaining budget makes a stalled
        recv abort exactly at the deadline. Guarded because the socket
        chain is implementation detail of urllib3 — the read slice
        bound stands regardless.
        """
        try:
            raw = response.raw
            fp = getattr(getattr(raw, "_fp", None), "fp", None)
            sock = getattr(getattr(fp, "raw", None), "_sock", None)
            if sock is None:
                sock = getattr(fp, "_sock", None)
            if sock is not None:
                sock.settimeout(max(0.05, float(remaining)))
        except (AttributeError, OSError, ValueError):
            return

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

    def _map_body(self, body: Any, duration_ms: int) -> ProviderInvocationPayload:
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
