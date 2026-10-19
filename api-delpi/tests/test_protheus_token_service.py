"""Tests — in-memory Protheus token reuse and expiry."""

from __future__ import annotations

from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.domain.integrations.protheus_rest import (
    ProtheusAccessToken,
    ProtheusRestConfig,
)


class _FakeGateway:
    def __init__(self) -> None:
        self.calls = 0

    def request_access_token(self, config: ProtheusRestConfig) -> ProtheusAccessToken:
        self.calls += 1
        return ProtheusAccessToken(
            access_token=f"tok-{self.calls}",
            expires_in=3600,
            obtained_at_monotonic=100.0,
        )


def _config() -> ProtheusRestConfig:
    return ProtheusRestConfig(
        username="u",
        password="p",
        base_url="https://example/rest",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/delpi/api/v1/suppliers/",
    )


def test_reuses_valid_token() -> None:
    clock = {"now": 100.0}
    gateway = _FakeGateway()
    service = ProtheusTokenService(
        gateway,  # type: ignore[arg-type]
        expiry_margin_seconds=60,
        monotonic=lambda: clock["now"],
    )
    first = service.get_valid_token(_config())
    clock["now"] = 500.0  # still within 3600-60
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
    clock["now"] = 100.0 + 3600 - 30  # inside margin → refresh
    token = service.get_valid_token(_config())
    assert token == "tok-2"
    assert gateway.calls == 2
