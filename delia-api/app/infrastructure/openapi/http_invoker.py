"""HTTP mechanics for the OpenAPI capability provider.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
all OpenAPI wire mechanics live here — document fetch, path
templating, query projection, subject-bearer propagation, bounded
response normalization. The orchestrator and the provider adapter
never see URLs, methods, or headers.

Fail closed:
- only GET (READ-class) invocations are executed — any other method
  is refused before any wire call;
- the subject bearer comes from the request-scoped accessor only —
  never persisted, logged, or modeled;
- responses are normalized into bounded OBSERVATION outcomes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlencode

from app.infrastructure.http.bounded_request import bounded_request
from app.application.capability_provision.contracts import (
    OWNER_ARGUMENT_REJECTED,
    OWNER_RECORD_NOT_FOUND,
    CapabilityProviderError,
    ProviderCapability,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

MAX_OPENAPI_RESPONSE_CHARS = 64_000
_OPENAPI_FETCH_TIMEOUT_SECONDS = 10.0
_PATH_PARAM = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _owner_not_found_hint(response: Any) -> str | None:
    """Owner absence declared by the shared not-found envelope.

    ``not_found_response`` answers HTTP 404 with ``success=false``,
    ``error.recoverable=false``, a non-empty ``error.code`` and a
    message. Any other 404 stays a transport failure.
    """
    if getattr(response, "status_code", 0) != 404:
        return None
    try:
        parsed = response.json()
    except Exception:
        return None
    if not isinstance(parsed, Mapping):
        return None
    if parsed.get("success") is not False:
        return None
    error = parsed.get("error")
    if not isinstance(error, Mapping):
        return None
    if error.get("recoverable") is not False:
        return None
    code = error.get("code")
    if not isinstance(code, str) or not code.strip():
        return None
    message = parsed.get("message")
    if not isinstance(message, str) or not message.strip():
        return None
    cleaned = "".join(
        ch if ch.isprintable() else " " for ch in message
    ).strip()
    if not cleaned:
        return None
    return cleaned[:240]


# Owner-published argument-validation error codes whose contract
# semantics authorize a reformulated READ (typed classification owned
# by the API — never inferred from message text). Only codes the
# owner actually emits may be listed here.
_OWNER_ARG_VALIDATION_CODES = frozenset({"VALIDATION_ERROR"})


def _owner_recoverable_rejection_hint(response: Any) -> str | None:
    """Owner argument rejection declared by the shared error envelope.

    Recoverable ONLY under explicit contractual evidence:

    - ``error.recoverable is True`` — the owner's ``error_response``
      declares the rejection repairable; or
    - ``error.code`` is an owner-published argument-validation code
      and ``recoverable`` is not negated — typed classification
      authorizing one reformulated READ.

    Absence of ``recoverable:false`` is NOT a declaration: a bare
    400/422, an envelope without an ``error`` block, a malformed
    body, or any non-declared shape fails closed as an ordinary
    invocation failure. The returned value is a sanitized message
    excerpt — untrusted owner data, never an instruction.
    """
    if getattr(response, "status_code", 0) not in (400, 422):
        return None
    try:
        parsed = response.json()
    except Exception:
        return None
    if not isinstance(parsed, Mapping):
        return None
    if parsed.get("success") is not False:
        return None
    error = parsed.get("error")
    if not isinstance(error, Mapping):
        return None
    recoverable = error.get("recoverable")
    if recoverable is not True:
        code = error.get("code")
        if not (
            recoverable is None
            and isinstance(code, str)
            and code in _OWNER_ARG_VALIDATION_CODES
        ):
            return None
    message = parsed.get("message")
    if not isinstance(message, str):
        return None
    cleaned = "".join(
        ch if ch.isprintable() else " " for ch in message
    ).strip()
    if not cleaned:
        return None
    return cleaned[:240]


def fetch_openapi_document(
    base_url: str,
    *,
    http_get: Callable,
    timeout_seconds: float = _OPENAPI_FETCH_TIMEOUT_SECONDS,
) -> Mapping[str, Any]:
    """Fetch one provider's live OpenAPI document (bounded).

    Raises CapabilityProviderError on any transport/parse failure —
    callers treat the source as unavailable, never as empty.
    """
    url = base_url.rstrip("/") + "/openapi.json"
    try:
        response = bounded_request(
            http_get,
            url,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        raise CapabilityProviderError(
            "openapi_document_unavailable", str(exc)[:200]
        ) from exc
    status = getattr(response, "status_code", None)
    if status != 200:
        raise CapabilityProviderError(
            "openapi_document_unavailable", f"status={status}"
        )
    try:
        document = response.json()
    except Exception as exc:
        raise CapabilityProviderError(
            "openapi_document_invalid", str(exc)[:200]
        ) from exc
    if not isinstance(document, Mapping):
        raise CapabilityProviderError(
            "openapi_document_invalid", "document is not an object"
        )
    return document


class HttpOpenApiInvoker:
    """Bounded GET-only invoker for one OpenAPI capability source.

    Reads the capability's opaque binding (operation_id, http_method,
    http_path, declared inputs) — the provider adapter fills it from
    the governed CapabilityProjection and this is the only place it is
    interpreted.
    """

    def __init__(
        self,
        base_url: str,
        *,
        source_id: str,
        subject_bearer_getter: Callable[[], str | None],
        http_get: Callable,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._source_id = source_id
        self._bearer = subject_bearer_getter
        self._http_get = http_get
        self._timeout = timeout_seconds

    def __call__(
        self,
        capability: ProviderCapability,
        arguments: Mapping[str, object],
        timeout_seconds: float | None = None,
    ) -> SpecialistOutcome:
        # Caller-bound reduction ceiling (LOOP-03R2A-R1): the
        # configured stage max is shortened, never lengthened.
        effective_timeout = (
            self._timeout
            if timeout_seconds is None
            else min(float(timeout_seconds), self._timeout)
        )
        binding = capability.binding
        method = str(binding.get("http_method") or "").upper()
        if method != "GET":
            # Non-GET OpenAPI capabilities are projected UNKNOWN upstream
            # and can never reach here — this is the belt, not the
            # boundary.
            raise CapabilityProviderError(
                "openapi_write_not_authorized",
                "non-read OpenAPI operations are not executable",
            )
        bearer = self._bearer()
        if not bearer:
            raise CapabilityProviderError(
                "mcp_authentication_failed",
                "subject bearer unavailable",
            )
        path = str(binding["http_path"])
        inputs = binding.get("inputs") or ()
        path_params: dict[str, object] = {}
        query: dict[str, object] = {}
        for descriptor in inputs:
            name = descriptor.get("name")
            if not isinstance(name, str) or name not in arguments:
                continue
            value = arguments[name]
            if descriptor.get("location") == "path":
                path_params[name] = value
            else:
                query[name] = value
        # Arguments not declared as inputs are dropped — the owner
        # contract is the only authority on what the wire carries.
        try:
            resolved_path = _PATH_PARAM.sub(
                lambda m: str(path_params[m.group(1)]), path
            )
        except KeyError as exc:
            raise CapabilityProviderError(
                "openapi_missing_path_parameter", str(exc)
            ) from exc
        url = self._base_url + resolved_path
        if query:
            url += "?" + urlencode(query, doseq=True)
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
        }
        try:
            response = bounded_request(
                self._http_get,
                url,
                headers=headers,
                timeout_seconds=effective_timeout,
            )
        except Exception as exc:
            raise CapabilityProviderError(
                "openapi_invocation_failed", str(exc)[:200]
            ) from exc
        status = getattr(response, "status_code", 0)
        if status in (401, 403):
            raise CapabilityProviderError(
                "mcp_authorization_denied",
                f"source denied the delegated call status={status}",
            )
        if status >= 400:
            not_found_hint = _owner_not_found_hint(response)
            if not_found_hint is not None:
                raise CapabilityProviderError(
                    OWNER_RECORD_NOT_FOUND,
                    f"status={status}",
                    owner_hint=not_found_hint,
                )
            rejection_hint = _owner_recoverable_rejection_hint(response)
            if rejection_hint is not None:
                raise CapabilityProviderError(
                    OWNER_ARGUMENT_REJECTED,
                    f"status={status}",
                    owner_hint=rejection_hint,
                )
            raise CapabilityProviderError(
                "openapi_invocation_failed", f"status={status}"
            )
        text = getattr(response, "text", "") or ""
        if len(text) > MAX_OPENAPI_RESPONSE_CHARS:
            text = text[:MAX_OPENAPI_RESPONSE_CHARS]
        structured: Mapping[str, object] | None = None
        try:
            parsed = response.json()
            if isinstance(parsed, Mapping):
                structured = parsed
        except Exception:
            structured = None
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id=self._source_id,
                remote_name=capability.remote_name,
                protocol=InteropProtocol.HTTP,
                correlation_id="",
                observed_at=_now_utc(),
            ),
            content_text=(
                text
                if structured is None
                else json.dumps(structured, ensure_ascii=False, default=str)
            ),
            is_complete=True,
            structured=structured,
        )
