"""Cliente HTTP S2S para observações MyWEG NF (retries só transitórios)."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from production_control_app.jobs.myweg_needs_publisher.http_client import redact_secrets

logger = logging.getLogger(__name__)

_TRANSIENT_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})
_NO_RETRY_STATUS = frozenset({401, 403, 409, 422})


@dataclass(frozen=True)
class InvoicePublishHttpResult:
    ok: bool
    status_code: int | None
    created: bool | None
    body: dict[str, Any] | None
    error: str | None
    attempts: int


class MyWegInvoiceObservationsPublisherClient:
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
    ) -> InvoicePublishHttpResult:
        url = f"{self._base_url}/integrations/myweg/invoice-observations"
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
                        "myweg_invoice_publisher_transient_error attempt=%s error=%s",
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
                    return InvoicePublishHttpResult(
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
                    return InvoicePublishHttpResult(
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
                return InvoicePublishHttpResult(
                    ok=False,
                    status_code=response.status_code,
                    created=None,
                    body=last_body,
                    error=redact_secrets(str(message), self._service_token),
                    attempts=attempts,
                )

        return InvoicePublishHttpResult(
            ok=False,
            status_code=last_status,
            created=None,
            body=last_body,
            error=last_error or "Falha transitória esgotou tentativas.",
            attempts=attempts,
        )

    def _backoff(self, attempt: int) -> None:
        base = min(8.0, 0.5 * (2 ** (attempt - 1)))
        jitter = random.uniform(0, 0.35)
        self._sleep(base + jitter)
