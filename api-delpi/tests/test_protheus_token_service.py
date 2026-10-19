"""Tests — in-memory Protheus token reuse, expiry and credential rotation."""

from __future__ import annotations

from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
    config_auth_fingerprint,
)
from app.domain.integrations.protheus_rest import (
    ProtheusAccessToken,
    ProtheusRestConfig,
)


class _FakeGateway:
    def __init__(self) -> None:
        self.calls = 0
        self.last_password: str | None = None

    def request_access_token(self, config: ProtheusRestConfig) -> ProtheusAccessToken:
        self.calls += 1
        self.last_password = config.password
        return ProtheusAccessToken(
            access_token=f"tok-{self.calls}",
            expires_in=3600,
            obtained_at_monotonic=100.0,
        )


def _config(**overrides: str) -> ProtheusRestConfig:
    values = {
        "username": "u",
        "password": "p",
        "base_url": "https://example/rest",
        "auth_path": "/api/oauth2/v1/token",
        "suppliers_path": "/delpi/api/v1/suppliers/",
    }
    values.update(overrides)
    return ProtheusRestConfig(**values)


def test_reuses_valid_token() -> None:
    clock = {"now": 100.0}
    gateway = _FakeGateway()
    service = ProtheusTokenService(
        gateway,  # type: ignore[arg-type]
        expiry_margin_seconds=60,
        monotonic=lambda: clock["now"],
    )
    first = service.get_valid_token(_config())
    clock["now"] = 500.0
    second = service.get_valid_token(_config())
    assert first == second == "tok-1"
    assert gateway.calls == 1


def test_refreshes_expired_token() -> None:
    clock = {"now": 100.0}
    gateway = _FakeGateway()
    service = ProtheusTokenService(
        gateway,  # type: ignore[arg-type]
        expiry_margin_seconds=60,
        monotonic=lambda: clock["now"],
    )
    service.get_valid_token(_config())
    clock["now"] = 100.0 + 3600 - 30
    token = service.get_valid_token(_config())
    assert token == "tok-2"
    assert gateway.calls == 2


def test_password_rotation_invalidates_cache() -> None:
    clock = {"now": 100.0}
    gateway = _FakeGateway()
    service = ProtheusTokenService(
        gateway,  # type: ignore[arg-type]
        expiry_margin_seconds=60,
        monotonic=lambda: clock["now"],
    )
    first = service.get_valid_token(_config(password="old-secret"))
    clock["now"] = 200.0
    second = service.get_valid_token(_config(password="new-secret"))
    assert first == "tok-1"
    assert second == "tok-2"
    assert gateway.calls == 2
    assert gateway.last_password == "new-secret"


def test_username_rotation_invalidates_cache() -> None:
    clock = {"now": 100.0}
    gateway = _FakeGateway()
    service = ProtheusTokenService(
        gateway,  # type: ignore[arg-type]
        expiry_margin_seconds=60,
        monotonic=lambda: clock["now"],
    )
    service.get_valid_token(_config(username="user-a"))
    token = service.get_valid_token(_config(username="user-b"))
    assert token == "tok-2"
    assert gateway.calls == 2


def test_fingerprint_never_contains_plaintext_password() -> None:
    config = _config(password="super-secret-value")
    fingerprint = config_auth_fingerprint(config)
    assert "super-secret-value" not in fingerprint
    assert config.username in fingerprint
    assert config.auth_url in fingerprint
