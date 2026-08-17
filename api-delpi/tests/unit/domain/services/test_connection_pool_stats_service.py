"""Payload agregado de connection pools para o console."""
from __future__ import annotations

from app.domain.services.connection_pool_stats_service import (
    build_connection_pool_stats_payload,
    get_connection_pool_stats_summary,
)


def test_build_connection_pool_stats_payload_shape() -> None:
    payload = build_connection_pool_stats_payload(
        plugins={
            "enabled": True,
            "max_size": 10,
            "created": 1,
            "available": 1,
            "in_use": 0,
            "acquire_timeout_seconds": 30,
            "acquire_timeouts_total": 0,
            "discards_total": 0,
            "application_name": "api-delpi-plugins",
        },
        totvs={
            "enabled": True,
            "max_size": 10,
            "created": 0,
            "available": 0,
            "in_use": 0,
            "acquire_timeout_seconds": 60,
            "acquire_timeouts_total": 0,
            "discards_total": 0,
        },
    )
    assert payload["plugins_postgres"]["max_size"] == 10
    assert payload["totvs"]["enabled"] is True
    assert payload["captured_at"]


def test_get_connection_pool_stats_summary_includes_plugins(monkeypatch) -> None:
    class _Pool:
        def stats(self):
            return {
                "enabled": True,
                "max_size": 3,
                "created": 0,
                "available": 0,
                "in_use": 0,
                "acquire_timeout_seconds": 30.0,
                "acquire_timeouts_total": 0,
                "discards_total": 0,
                "application_name": "api-delpi-plugins",
            }

    monkeypatch.setattr(
        "app.domain.services.connection_pool_stats_service.get_plugins_connection_pool",
        lambda: _Pool(),
    )
    monkeypatch.setattr(
        "app.domain.services.connection_pool_stats_service.get_totvs_connection_pool",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.domain.services.connection_pool_stats_service.TOTVS_POOL_ENABLED",
        False,
    )

    payload = get_connection_pool_stats_summary()
    assert payload["plugins_postgres"]["max_size"] == 3
    assert payload["totvs"]["enabled"] is False
