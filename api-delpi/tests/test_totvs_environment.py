"""TOTVS logical environment selector (TOTVS_TARGET_ENV) — isolated tests.

No real ERP connections: all cases exercise configuration resolution only.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.infrastructure.providers.totvs.environment import (
    TOTVS_ENVIRONMENT_CATALOG,
    resolve_totvs_environment,
)


@pytest.fixture
def restore_settings(monkeypatch):
    yield monkeypatch


def _set_all(monkeypatch, **kwargs):
    defaults = {
        "TOTVS_TARGET_ENV": None,
        "TOTVS_DB_DATABASE": None,
        "DB_DATABASE": "PGDB",
        "INTRANET_PARAMS_AMBIENTE": None,
        "PROTHEUS_REST_EXPECTED_BASE_URL": None,
    }
    defaults.update(kwargs)
    for key, value in defaults.items():
        monkeypatch.setattr(settings, key, value)


def test_tst01_resolves_tst_catalog(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01")
    profile = resolve_totvs_environment()
    assert profile.target_environment == "TST01"
    assert profile.sql_database == "DELPI_TST01"
    assert profile.rest_parameter_environment == "2"
    assert profile.sql_read_enabled is True


def test_prod_resolves_prod_catalog(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="PROD")
    profile = resolve_totvs_environment()
    assert profile.target_environment == "PROD"
    assert profile.sql_database == "DELPI"
    assert profile.rest_parameter_environment == "1"


def test_selector_is_case_insensitive(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="  prod ")
    assert resolve_totvs_environment().sql_database == "DELPI"


def test_invalid_selector_fails_closed(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="SANDBOX")
    with pytest.raises(RuntimeError, match="TOTVS_TARGET_ENV"):
        resolve_totvs_environment()


def test_divergent_database_fails_closed(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="TST01",
        TOTVS_DB_DATABASE="DELPI",  # contradiz catalogo TST01
    )
    with pytest.raises(RuntimeError, match="divergente"):
        resolve_totvs_environment()


def test_divergent_ambiente_fails_closed(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="PROD",
        INTRANET_PARAMS_AMBIENTE="2",
    )
    with pytest.raises(RuntimeError, match="divergente"):
        resolve_totvs_environment()


def test_matching_explicit_values_accepted(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="PROD",
        TOTVS_DB_DATABASE="DELPI",
        INTRANET_PARAMS_AMBIENTE="1",
    )
    profile = resolve_totvs_environment()
    assert profile.sql_database == "DELPI"
    assert profile.rest_parameter_environment == "1"


def test_legacy_mode_unset_selector_preserves_behavior(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_DB_DATABASE="DELPI",
        INTRANET_PARAMS_AMBIENTE="2",
        PROTHEUS_REST_EXPECTED_BASE_URL="http://x/rest",
    )
    profile = resolve_totvs_environment()
    assert profile.target_environment is None
    assert profile.sql_database == "DELPI"
    assert profile.rest_parameter_environment == "2"
    assert profile.rest_write_eligible is True


def test_legacy_disabled_database_marks_read_disabled(monkeypatch):
    _set_all(monkeypatch, TOTVS_DB_DATABASE="DISABLED", DB_DATABASE=None)
    profile = resolve_totvs_environment()
    assert profile.sql_read_enabled is False


def test_write_pin_stays_independent(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="TST01",
        PROTHEUS_REST_EXPECTED_BASE_URL="http://192.168.1.233:8701/rest",
    )
    profile = resolve_totvs_environment()
    # Selector never fabricates the write pin — it must exist independently.
    assert profile.expected_rest_base_url == "http://192.168.1.233:8701/rest"
    assert profile.rest_write_eligible is True


def test_catalog_has_only_approved_environments():
    assert set(TOTVS_ENVIRONMENT_CATALOG) == {"TST01", "PROD"}
