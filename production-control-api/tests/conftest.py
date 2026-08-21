"""Fixtures compartilhadas dos testes da production-control-api."""

from __future__ import annotations

import pytest

from production_control_app.application.services.machine_load_live_status_cache import (
    clear_live_status_cache,
)


@pytest.fixture(autouse=True)
def _reset_machine_load_live_status_cache() -> None:
    """O cache de status HZA é global por filial — cada teste começa frio."""
    clear_live_status_cache()
    yield
    clear_live_status_cache()
