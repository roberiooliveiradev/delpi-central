"""Cliente HTTP S2S com retries apenas para falhas transitórias."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

_TRANSIENT_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})
_NO_RETRY_STATUS = frozenset({401, 403, 409, 422})


@dataclass(frozen=True)
class PublishHttpResult:
    ok: bool
    status_code: int | None
    created: bool | None
    body: dict[str, Any] | None
    error: str | None
    attempts: int


@dataclass(frozen=True)
class Sb1ResolveHttpResult:
    ok: bool
    status_code: int | None
    body: dict[str, Any] | None
    error: str | None
    attempts: int
    skipped: bool
    persisted: bool


def redact_secrets(text: str, token: str) -> str:
    if not text:
        return text
    redacted = text
    if token:
        redacted = redacted.replace(token, "***REDACTED***")
        if token.startswith("Bearer "):
            redacted = redacted.replace(token[7:], "***REDACTED***")
    return redacted


class MyWegNeedsPublisherClient:
    def __init__(
        self,
        *,
        base_url: str,
        service_token: str,
        caller_app: str,
        timeout_seconds: float = 60.0,
        max_attempts: int = 3,
        sleep_fn: Callable[[float], None] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._caller_app = caller_app
        self._timeout = timeout_seconds
        self._max_attempts = max(1, max_attempts)
        self._sleep = sleep_fn or time.sleep
        self._transport = transport

    def publish(
        self,
        payload: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> PublishHttpResult:
        url = f"{self._base_url}/integrations/myweg/need-batches"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Delpi-Service-Token": self._service_token,
            "X-Delpi-Caller-App": self._caller_app,
            "Idempotency-Key": idempotency_key,
        }
        attempts = 0
        last_error: str | None = None
        last_status: int | None = None
        last_body: dict[str, Any] | None = None

        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            while attempts < self._max_attempts:
                attempts += 1
                try:
                    response = client.post(url, json=payload, headers=headers)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = redact_secrets(
                        f"{exc.__class__.__name__}", self._service_token
                    )
                    logger.warning(
                        "myweg_publisher_transient_error attempt=%s error=%s",
                        attempts,
                        last_error,
                    )
                    if attempts >= self._max_attempts:
                        break
                    self._backoff(attempts)
                    continue

                last_status = response.status_code
                try:
                    last_body = response.json()
                except ValueError:
                    last_body = None

                if response.status_code in {200, 201}:
                    data = (last_body or {}).get("data") or {}
                    return PublishHttpResult(
                        ok=True,
                        status_code=response.status_code,
                        created=bool(data.get("created"))
                        if "created" in data
                        else response.status_code == 201,
                        body=last_body,
                        error=None,
                        attempts=attempts,
                    )

                if response.status_code in _NO_RETRY_STATUS:
                    message = (last_body or {}).get("message") or response.reason_phrase
                    return PublishHttpResult(
                        ok=False,
                        status_code=response.status_code,
                        created=None,
                        body=last_body,
                        error=redact_secrets(str(message), self._service_token),
                        attempts=attempts,
                    )

                if response.status_code in _TRANSIENT_STATUS:
                    last_error = f"HTTP {response.status_code}"
                    if attempts >= self._max_attempts:
                        break
                    self._backoff(attempts)
                    continue

                message = (last_body or {}).get("message") or response.reason_phrase
                return PublishHttpResult(
                    ok=False,
                    status_code=response.status_code,
                    created=None,
                    body=last_body,
                    error=redact_secrets(str(message), self._service_token),
                    attempts=attempts,
                )

        return PublishHttpResult(
            ok=False,
            status_code=last_status,
            created=None,
            body=last_body,
            error=last_error or "Falha transitória esgotou tentativas.",
            attempts=attempts,
        )

    def resolve_sb1(
        self,
        *,
        collection_id: str,
        dry_run: bool = False,
        skip_if_complete: bool = True,
    ) -> Sb1ResolveHttpResult:
        """POST E4 S2S — resolução SB1 do lote já ingerido."""
        url = f"{self._base_url}/integrations/myweg/need-batches/sb1-resolve"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Delpi-Service-Token": self._service_token,
            "X-Delpi-Caller-App": self._caller_app,
        }
        payload = {
            "collection_id": collection_id,
            "dry_run": dry_run,
            "skip_if_complete": skip_if_complete,
        }
        attempts = 0
        last_error: str | None = None
        last_status: int | None = None
        last_body: dict[str, Any] | None = None

        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            while attempts < self._max_attempts:
                attempts += 1
                try:
                    response = client.post(url, json=payload, headers=headers)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = redact_secrets(
                        f"{exc.__class__.__name__}", self._service_token
                    )
                    logger.warning(
                        "myweg_sb1_resolve_transient_error attempt=%s error=%s",
                        attempts,
                        last_error,
                    )
                    if attempts >= self._max_attempts:
                        break
                    self._backoff(attempts)
                    continue

                last_status = response.status_code
                try:
                    last_body = response.json()
                except ValueError:
                    last_body = None

                if response.status_code in {200, 201}:
                    data = (last_body or {}).get("data") or {}
                    return Sb1ResolveHttpResult(
                        ok=True,
                        status_code=response.status_code,
                        body=last_body,
                        error=None,
                        attempts=attempts,
                        skipped=bool(data.get("skipped")),
                        persisted=bool(data.get("persisted")),
                    )

                if response.status_code in _NO_RETRY_STATUS:
                    message = (last_body or {}).get("message") or response.reason_phrase
                    return Sb1ResolveHttpResult(
                        ok=False,
                        status_code=response.status_code,
                        body=last_body,
                        error=redact_secrets(str(message), self._service_token),
                        attempts=attempts,
                        skipped=False,
                        persisted=False,
                    )

                if response.status_code in _TRANSIENT_STATUS:
                    last_error = f"HTTP {response.status_code}"
                    if attempts >= self._max_attempts:
                        break
                    self._backoff(attempts)
                    continue

                message = (last_body or {}).get("message") or response.reason_phrase
                return Sb1ResolveHttpResult(
                    ok=False,
                    status_code=response.status_code,
                    body=last_body,
                    error=redact_secrets(str(message), self._service_token),
                    attempts=attempts,
                    skipped=False,
                    persisted=False,
                )

        return Sb1ResolveHttpResult(
            ok=False,
            status_code=last_status,
            body=last_body,
            error=last_error or "Falha transitória SB1 esgotou tentativas.",
            attempts=attempts,
            skipped=False,
            persisted=False,
        )

    def _backoff(self, attempt: int) -> None:
        base = min(8.0, 0.5 * (2 ** (attempt - 1)))
        jitter = random.uniform(0, 0.35)
        self._sleep(base + jitter)
