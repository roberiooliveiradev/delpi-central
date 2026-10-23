"""OpenAI-compatible audio transcription adapter — VD-F03.

POST {base_url}/chat/completions with an ``input_audio`` content part,
behind ``SpeechTranscriptionPort``. Same approved provider family as
DÉLIA model invocation (e.g. OpenRouter) with a dedicated audio-capable
model from config — never hardcoded, never the interaction model.

The API key is only used for the provider Authorization header and is
never logged or embedded in errors. Audio bytes never appear in logs.
The transcription instruction is provider-bound prompt data (pt-BR
verbatim), not UI copy — a constant here, not a content-layer concern
for the single-consumer dictation contract.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any, Callable, Iterator

import requests

from app.application.dictation.errors import (
    PROVIDER_REJECTED,
    PROVIDER_TIMEOUT,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
    DictationError,
)
from app.application.ports.speech_transcription_port import (
    SpeechTranscriptionRequest,
)
from app.infrastructure.http.bounded_request import (
    BoundedHttpTimeout,
    BoundedHttpTooLarge,
    BoundedHttpTransportError,
    bounded_request,
)
from app.infrastructure.http.deadline_transport import deadline_http_post

_TRANSCRIPTION_INSTRUCTION = (
    "Transcreva exatamente a fala em português brasileiro (pt-BR). "
    "Responda somente com o texto transcrito, sem aspas, sem comentários, "
    "sem tradução e sem formatação adicional. Se o áudio não contiver "
    "fala inteligível, responda com texto vazio."
)


class OpenAICompatibleTranscriptionAdapter:
    """Audio→text via OpenAI-compatible chat completions + input_audio."""

    ADAPTER_KIND = "OPENAI_COMPATIBLE_AUDIO"

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
                raise ValueError(f"stt provider configuration missing {name}")
        if timeout_seconds <= 0:
            raise ValueError("stt provider timeout_seconds must be > 0")
        self._endpoint = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = float(timeout_seconds)
        self._http_post = http_post

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    def transcribe(self, request: SpeechTranscriptionRequest) -> str:
        timeout = self._timeout_seconds
        audio_b64 = base64.b64encode(request.audio_bytes).decode("ascii")
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": _TRANSCRIPTION_INSTRUCTION,
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": request.provider_format,
                            },
                        },
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 2048,
            "stream": False,
        }
        try:
            # bounded_request enforces the TOTAL wall-clock deadline —
            # connect, status line, headers and body drain share it.
            response = bounded_request(
                self._http_post,
                self._endpoint,
                timeout_seconds=timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            self._check_status(response.status_code)
            body = response.json()
        except DictationError:
            raise
        except BoundedHttpTimeout as exc:
            raise DictationError(
                PROVIDER_TIMEOUT, "transcription provider timed out"
            ) from exc
        except (
            BoundedHttpTransportError,
            BoundedHttpTooLarge,
            requests.exceptions.RequestException,
            json.JSONDecodeError,
        ) as exc:
            raise DictationError(
                PROVIDER_UNAVAILABLE, "transcription provider unreachable"
            ) from exc
        return self._map_body(body)

    def stream_transcribe(
        self, request: SpeechTranscriptionRequest
    ) -> Iterator[str]:
        """dictation.incremental.v1 — real provider SSE deltas.

        Yields cumulative transcript snapshots as the provider streams
        them (``stream: true`` chat completions). Every snapshot is real
        provider output — never fabricated or timer-driven text. The
        total wall-clock deadline mirrors ``transcribe``: connect, SSE
        lines and drain share ``self._timeout_seconds``.
        """
        timeout = self._timeout_seconds
        deadline = time.monotonic() + timeout
        audio_b64 = base64.b64encode(request.audio_bytes).decode("ascii")
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": _TRANSCRIPTION_INSTRUCTION,
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": request.provider_format,
                            },
                        },
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 2048,
            "stream": True,
        }
        try:
            response = requests.post(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                json=payload,
                stream=True,
                timeout=(min(10.0, timeout), timeout),
            )
        except requests.exceptions.RequestException as exc:
            raise DictationError(
                PROVIDER_UNAVAILABLE, "transcription provider unreachable"
            ) from exc
        try:
            self._check_status(response.status_code)
            cumulative = ""
            for raw in response.iter_lines(decode_unicode=True):
                if time.monotonic() > deadline:
                    raise DictationError(
                        PROVIDER_TIMEOUT,
                        "transcription provider timed out",
                    )
                if not raw:
                    continue
                line = raw.strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = self._map_delta(chunk)
                if not delta:
                    continue
                cumulative += delta
                yield cumulative
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _map_delta(chunk: Any) -> str:
        if not isinstance(chunk, dict):
            return ""
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        delta = first.get("delta")
        if not isinstance(delta, dict):
            return ""
        content = delta.get("content")
        return content if isinstance(content, str) else ""

    @staticmethod
    def _check_status(status_code: int) -> None:
        if status_code == 200:
            return
        if status_code == 429:
            raise DictationError(
                RATE_LIMITED, "transcription provider rate limit"
            )
        if 400 <= status_code < 500:
            raise DictationError(
                PROVIDER_REJECTED,
                f"transcription provider rejected the request "
                f"(HTTP {status_code})",
            )
        raise DictationError(
            PROVIDER_UNAVAILABLE,
            f"transcription provider unavailable (HTTP {status_code})",
        )

    @staticmethod
    def _map_body(body: Any) -> str:
        if not isinstance(body, dict):
            raise DictationError(
                PROVIDER_UNAVAILABLE,
                "transcription provider returned an invalid body",
            )
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise DictationError(
                PROVIDER_UNAVAILABLE,
                "transcription provider returned no choices",
            )
        message = choices[0].get("message") if isinstance(
            choices[0], dict
        ) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            return content
        # Some providers return content parts; only text parts are
        # admissible for a transcript — anything else is untranscribable.
        if isinstance(content, list):
            parts = [
                part.get("text")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            return "".join(p for p in parts if isinstance(p, str))
        return ""
