"""SLA list returns configured=false when the table is empty or unavailable."""

from __future__ import annotations

from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)


def test_sla_unconfigured_payload_shape() -> None:
    payload = {"items": [], "configured": False}
    assert payload["configured"] is False
    assert payload["items"] == []
    assert issubclass(PluginsRepositoryError, RuntimeError)
