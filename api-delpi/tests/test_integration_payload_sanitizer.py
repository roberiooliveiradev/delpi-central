"""Sanitizer tests — redaction policy, truncation, canonical hashing."""

from __future__ import annotations

from app.application.services.integration_tracking.payload_sanitizer import (
    MAX_STRING_LENGTH,
    REDACTED,
    build_error_details,
    build_outbound_payload,
    build_request_payload,
    build_response_payload,
    canonical_hash,
    enforce_size_limit,
    sanitize_fields,
    sanitize_value,
)


def test_sensitive_fields_are_redacted() -> None:
    fields = {
        "supplier_name": "ACME LTDA",
        "supplier_short_name": "ACME",
        "tax_id": "98887766000134",
        "email": "compras@acme.test",
        "phone": "4799999999",
        "contact_name": "JOSE",
        "state_registration": "123456",
        "municipal_registration": "654321",
        "codusr": "000311",
    }
    sanitized = sanitize_fields(fields)
    assert sanitized["supplier_name"] == "ACME LTDA"
    assert sanitized["supplier_short_name"] == "ACME"
    for key in (
        "tax_id",
        "email",
        "phone",
        "contact_name",
        "state_registration",
        "municipal_registration",
        "codusr",
    ):
        assert sanitized[key] == REDACTED


def test_request_payload_shape() -> None:
    payload = build_request_payload(
        {"supplier_name": "ACME", "tax_id": "123"}
    )
    assert payload["schema_version"] == 1
    assert payload["fields"]["supplier_name"] == "ACME"
    assert payload["fields"]["tax_id"] == REDACTED
    assert payload["submitted_fields"] == ["supplier_name", "tax_id"]


def test_outbound_payload_redacts_codusr_inside_body() -> None:
    body = {
        "codusr": "000311",
        "fornecedor": {"supplier_name": "ACME", "phone": "479999"},
    }
    payload = build_outbound_payload(
        method="PUT", resource="supplier", resource_key="00387801", body=body
    )
    assert payload["method"] == "PUT"
    assert payload["resource_key"] == "00387801"
    assert payload["body"]["codusr"] == REDACTED
    assert payload["body"]["fornecedor"]["supplier_name"] == "ACME"
    # PII is redacted at any depth — even inside the upstream fornecedor body.
    assert payload["body"]["fornecedor"]["phone"] == REDACTED


def test_long_strings_truncated() -> None:
    value = "x" * (MAX_STRING_LENGTH + 50)
    assert sanitize_value(value).endswith("...[TRUNCATED]")
    assert len(sanitize_value(value)) <= MAX_STRING_LENGTH + len(
        "...[TRUNCATED]"
    )


def test_nested_structures_sanitized() -> None:
    data = {"list": [{"token": "abc"}, 123, None], "nested": {"ok": True}}
    out = sanitize_value(data)
    assert out["list"][1] == 123
    assert out["nested"]["ok"] is True


def test_response_payload_extracts_message() -> None:
    payload = build_response_payload(
        http_status=200, body={"mensagem": "Fornecedor alterado com sucesso."}
    )
    assert payload["http_status"] == 200
    assert payload["message"] == "Fornecedor alterado com sucesso."


def test_error_details_never_store_raw() -> None:
    details = build_error_details(
        category="INDETERMINATE_OUTCOME",
        code="PROTHEUS_TIMEOUT",
        message="timeout after 30s",
        retry_safe=False,
    )
    assert details["retry_safe"] is False
    assert details["raw_error_stored"] is False


def test_canonical_hash_stable_and_sensitive_to_content() -> None:
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert canonical_hash(a, key="k") == canonical_hash(b, key="k")
    assert canonical_hash(a, key="k") != canonical_hash({"a": 3, "b": 1}, key="k")


def test_canonical_hash_is_keyed_not_plain_sha256() -> None:
    payload = {"tax_id": "98887766000134"}
    import hashlib
    import json

    plain = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    digest = canonical_hash(payload, key="server-secret")
    assert digest is not None
    assert digest != plain  # keyed HMAC — dictionary lookup does not apply
    assert canonical_hash(payload, key="other") != digest


def test_canonical_hash_without_key_returns_none() -> None:
    # With no key configured at all the result must be None, never plain hash.
    import os

    saved_secret = os.environ.pop("INTEGRATION_TRACKING_HMAC_SECRET", None)
    saved_jwt = os.environ.pop("JWT_SECRET", None)
    try:
        assert canonical_hash({"a": 1}) is None
    finally:
        if saved_secret:
            os.environ["INTEGRATION_TRACKING_HMAC_SECRET"] = saved_secret
        if saved_jwt:
            os.environ["JWT_SECRET"] = saved_jwt


def test_enforce_size_limit_keeps_small_payload() -> None:
    small = {"a": "b"}
    assert enforce_size_limit(small) == small
    assert enforce_size_limit(None) is None


def test_enforce_size_limit_drops_oversized() -> None:
    huge = {"blob": "y" * 40000}
    out = enforce_size_limit(huge)
    assert out["oversized"] is True
    assert "blob" not in out


def test_malicious_payload_stays_inert() -> None:
    """Injection-looking strings persist as data, never executed."""
    payload = build_request_payload(
        {"supplier_name": "'; DROP TABLE integration_operations;--"}
    )
    assert (
        payload["fields"]["supplier_name"]
        == "'; DROP TABLE integration_operations;--"
    )
