from __future__ import annotations

import pytest

from tm_app.application.services.dashboard_query_cache import dashboard_query_cache


@pytest.fixture(autouse=True)
def _reset_dashboard_query_cache():
    """Isola o cache de consultas do dashboard (singleton de processo) entre testes."""
    dashboard_query_cache.invalidate()
    yield
    dashboard_query_cache.invalidate()
