"""Sanitization and canonical hashing for tracked integration payloads.

Policy (documented in docs/integrations/protheus-write-execution-tracking.md):
- Supplier names/address are business data → stored.
- Personal data (contact_name, email, phone, tax id, registrations) and the
  Protheus codusr inside bodies → fully redacted.
- Secrets/auth material are never stored (they never enter these helpers —
  tokens stay in the token service; outbound bodies never carry headers).
- All stored strings are length-capped; malicious control bytes are kept
  harmless because payloads persist as JSONB, never executed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

PAYLOAD_SCHEMA_VERSION = 1
REDACTED = "[REDACTED]"
MAX_STRING_LENGTH = 300
MAX_JSON_BYTES = 16384

# Field names whose values are redacted wherever they appear in a payload.
SENSITIVE_FIELD_NAMES = frozenset(
    {
        "tax_id",
        "email",
        "phone",
        "area_code",
        "contact_name",
        "state_registration",
        "municipal_registration",
        "codusr",
        "password",
        "senha",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "client_secret",
        "psw_protheus",
        "usr_protheus",
    }
)


def _truncate(value: str) -> str:
    if len(value) <= MAX_STRING_LENGTH:
        return value
    return value[:MAX_STRING_LENGTH] + "...[TRUNCATED]"


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize; sensitive keys are redacted at ANY depth."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_FIELD_NAMES:
                out[str(key)] = REDACTED
            else:
                out[str(key)] = sanitize_value(item)
        return out
    if isinstance(value, (list, tuple)):
        return [sanitize_value(v) for v in value]
    if isinstance(value, str):
        return _truncate(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _truncate(str(value))


def sanitize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a flat supplier-fields mapping, honoring the redaction list."""
    return sanitize_value(fields)


def build_request_payload(fields: dict[str, Any]) -> dict:
    """Sanitized view of what the caller asked to write."""
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "fields": sanitize_fields(fields),
        "submitted_fields": sorted(str(k) for k in fields.keys()),
    }


def build_outbound_payload(
    *,
    method: str,
    resource: str,
    resource_key: str | None,
    body: dict[str, Any],
) -> dict:
    """Sanitized view of the exact upstream body shape sent by the gateway."""
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "method": method,
        "resource": resource,
        "resource_key": resource_key,
        "body": sanitize_value(body),
    }


def build_response_payload(
    *, http_status: int | None, body: dict[str, Any] | None
) -> dict:
    """Sanitized upstream response. Keeps message/code, never raw internals."""
    upstream_code = None
    message = None
    if isinstance(body, dict):
        for key in ("codigo", "code", "error", "status"):
            if body.get(key):
                upstream_code = str(body[key])[:200]
                break
        for key in ("mensagem", "message", "detail"):
            if body.get(key):
                message = str(body[key])[:MAX_STRING_LENGTH]
                break
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "http_status": http_status,
        "message": message,
        "upstream_code": upstream_code,
    }


def build_error_details(
    *,
    category: str,
    code: str,
    message: str,
    retry_safe: bool,
    http_status: int | None = None,
) -> dict:
    """Stable sanitized error JSON — raw upstream text is never stored."""
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "category": category,
        "code": code[:200],
        "message": _truncate(message),
        "http_status": http_status,
        "retry_safe": bool(retry_safe),
        "raw_error_stored": False,
    }


def build_confirmation_evidence(
    *,
    method: str,
    resource_key: str | None,
    environment_key: str | None,
    checked_fields: list[str],
    result: str,
) -> dict:
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "method": method,
        "resource_key": resource_key,
        "environment_key": environment_key,
        "checked_fields": checked_fields,
        "result": result,
    }


def canonical_hash(payload: Any) -> str:
    """SHA-256 over canonical JSON (sorted keys) — stable dedup/audit anchor."""
    canonical = json.dumps(
        sanitize_value(payload),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def enforce_size_limit(payload: dict | None) -> dict | None:
    """Drop payload to a minimal stub when it exceeds the storage budget."""
    if payload is None:
        return None
    encoded = json.dumps(payload, ensure_ascii=True, default=str).encode("utf-8")
    if len(encoded) <= MAX_JSON_BYTES:
        return payload
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "oversized": True,
        "omitted_bytes": len(encoded),
    }
