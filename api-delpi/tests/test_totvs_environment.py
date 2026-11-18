"""TOTVS logical environment selector (TOTVS_TARGET_ENV) — isolated tests.

No real ERP connections: all cases exercise configuration resolution only.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.infrastructure.providers.totvs.environment import (
    TOTVS_ENVIRONMENT_CATALOG,
    TotvsEnvironmentProfile,
    resolve_totvs_environment,
)
from app.infrastructure.providers.totvs import connection_pool


@pytest.fixture(autouse=True)
def _reset_pool_freeze():
    connection_pool._reset_totvs_environment_freeze()
    yield
    connection_pool._reset_totvs_environment_freeze()


def _set_all(monkeypatch, **kwargs):
    defaults = {
        "TOTVS_TARGET_ENV": None,
        "API_ENV": "development",
        "TOTVS_DB_DATABASE": None,
        "DB_DATABASE": "PGDB",
        "TOTVS_DB_HOST": "sqlserver",
        "DB_HOST": "pg",
        "TOTVS_DB_PORT": "1433",
        "DB_PORT": "5432",
        "TOTVS_DB_USER": "u",
        "DB_USER": "u",
        "TOTVS_DB_PASSWORD": "p",
        "DB_PASSWORD": "p",
        "INTRANET_PARAMS_AMBIENTE": None,
        "PROTHEUS_REST_EXPECTED_BASE_URL": None,
    }
    defaults.update(kwargs)
    for key, value in defaults.items():
        monkeypatch.setattr(settings, key, value)


# ---------- RQ-01 — runtime authorization matrix ----------

def test_dev_tst01_resolves_tst_catalog(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01", API_ENV="development")
    profile = resolve_totvs_environment()
    assert profile.target_environment == "TST01"
    assert profile.runtime_environment == "DEV"
    assert profile.sql_database == "DELPI_TST01"
    assert profile.rest_parameter_environment == "2"
    assert profile.sql_read_enabled is True


def test_hml_tst01_resolves_tst_catalog(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01", API_ENV="homologation")
    profile = resolve_totvs_environment()
    assert profile.runtime_environment == "HML"
    assert profile.sql_database == "DELPI_TST01"
    assert profile.rest_parameter_environment == "2"


def test_prod_prod_resolves_prod_catalog(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="PROD", API_ENV="production")
    profile = resolve_totvs_environment()
    assert profile.target_environment == "PROD"
    assert profile.sql_database == "DELPI"
    assert profile.rest_parameter_environment == "1"


def test_dev_prod_blocked_by_default(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="PROD", API_ENV="development")
    with pytest.raises(RuntimeError, match="não autorizado"):
        resolve_totvs_environment()


def test_hml_prod_blocked(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="PROD", API_ENV="homologation")
    with pytest.raises(RuntimeError, match="não autorizado"):
        resolve_totvs_environment()


def test_prod_tst01_blocked_without_explicit_policy(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01", API_ENV="production")
    with pytest.raises(RuntimeError, match="não autorizado"):
        resolve_totvs_environment()


def test_unclassifiable_runtime_cannot_use_selector(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01", API_ENV="moon-base")
    with pytest.raises(RuntimeError, match="não autorizado"):
        resolve_totvs_environment()


def test_invalid_selector_fails_closed(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="SANDBOX", API_ENV="production")
    with pytest.raises(RuntimeError, match="TOTVS_TARGET_ENV"):
        resolve_totvs_environment()


# ---------- RQ-01/RQ-02 — divergence and disabled database ----------

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
        API_ENV="production",
        INTRANET_PARAMS_AMBIENTE="2",
    )
    with pytest.raises(RuntimeError, match="divergente"):
        resolve_totvs_environment()


def test_matching_explicit_values_accepted(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="PROD",
        API_ENV="production",
        TOTVS_DB_DATABASE="DELPI",
        INTRANET_PARAMS_AMBIENTE="1",
    )
    profile = resolve_totvs_environment()
    assert profile.sql_database == "DELPI"
    assert profile.rest_parameter_environment == "1"


def test_legacy_disabled_database_marks_read_disabled(monkeypatch):
    _set_all(monkeypatch, TOTVS_DB_DATABASE="DISABLED", DB_DATABASE=None)
    profile = resolve_totvs_environment()
    assert profile.sql_read_enabled is False


def test_disabled_database_blocks_connection_string(monkeypatch):
    _set_all(monkeypatch, TOTVS_DB_DATABASE="DISABLED", DB_DATABASE=None)
    with pytest.raises(RuntimeError, match="desabilitada|não resolvido"):
        connection_pool.build_totvs_connection_string()


def test_disabled_database_does_not_fallback_to_db_database(monkeypatch):
    _set_all(
        monkeypatch, TOTVS_DB_DATABASE="DISABLED", DB_DATABASE="SHOULD_NOT_USE"
    )
    with pytest.raises(RuntimeError):
        connection_pool.build_totvs_connection_string()


# ---------- RQ-03 — independent REST pin ----------

def test_write_pin_stays_independent(monkeypatch):
    _set_all(
        monkeypatch,
        TOTVS_TARGET_ENV="TST01",
        PROTHEUS_REST_EXPECTED_BASE_URL="http://192.168.1.233:8701/rest",
    )
    profile = resolve_totvs_environment()
    # O seletor nunca fabrica o pin de escrita — ele deve existir
    # independentemente; sua presença não autoriza escrita.
    assert profile.expected_rest_base_url == "http://192.168.1.233:8701/rest"
    assert profile.rest_write_pin_configured is True


def test_pin_absent_marks_not_configured_not_ineligible_write(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01")
    profile = resolve_totvs_environment()
    assert profile.rest_write_pin_configured is False


# ---------- RQ-04 — pool environment immutability ----------

def test_pool_profile_is_frozen_per_process(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01")
    assert connection_pool.build_totvs_connection_string()

    monkeypatch.setattr(settings, "TOTVS_TARGET_ENV", None)
    monkeypatch.setattr(settings, "TOTVS_DB_DATABASE", "DELPI")
    with pytest.raises(RuntimeError, match="imutável"):
        connection_pool.build_totvs_connection_string()


def test_stable_resolution_reuses_frozen_profile(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01")
    s1 = connection_pool.build_totvs_connection_string()
    s2 = connection_pool.build_totvs_connection_string()
    assert s1 == s2


def test_connection_string_targets_tst01(monkeypatch):
    _set_all(monkeypatch, TOTVS_TARGET_ENV="TST01")
    conn = connection_pool.build_totvs_connection_string()
    assert "DATABASE=DELPI_TST01" in conn


def test_no_prod_fallback_when_database_missing(monkeypatch):
    _set_all(monkeypatch, TOTVS_DB_DATABASE=None, DB_DATABASE=None)
    with pytest.raises(RuntimeError, match="desabilitada|não resolvido"):
        connection_pool.build_totvs_connection_string()


# ---------- legacy compatibility ----------

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
    assert profile.rest_write_pin_configured is True


def test_legacy_connection_string_uses_totvs_database(monkeypatch):
    _set_all(monkeypatch, TOTVS_DB_DATABASE="DELPI")
    conn = connection_pool.build_totvs_connection_string()
    assert "DATABASE=DELPI" in conn


def test_catalog_has_only_approved_environments():
    assert set(TOTVS_ENVIRONMENT_CATALOG) == {"TST01", "PROD"}


# ---------- RQ-06 — SA5 get_supplier_link identity ----------

def test_get_supplier_link_returns_none_when_absent(monkeypatch):
    from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import (
        ProductSuppliersRepository,
    )

    monkeypatch.setattr(
        ProductSuppliersRepository, "_connect", lambda self: None
    )
    monkeypatch.setattr(
        ProductSuppliersRepository, "_close", lambda self, discard=False: None
    )
    repo = ProductSuppliersRepository()
    monkeypatch.setattr(repo, "execute_query", lambda *a, **k: [])
    identity = dict(
        product_code="P", supplier_code="F", supplier_store="01",
        manufacturer_code="M", manufacturer_store="01",
        grade_reference="", branch="01",
    )
    assert repo.get_supplier_link(**identity) is None


def test_get_supplier_link_raises_on_duplicate_identity(monkeypatch):
    from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import (
        ProductSuppliersRepository,
    )

    monkeypatch.setattr(
        ProductSuppliersRepository, "_connect", lambda self: None
    )
    monkeypatch.setattr(
        ProductSuppliersRepository, "_close", lambda self, discard=False: None
    )
    repo = ProductSuppliersRepository()
    monkeypatch.setattr(repo, "execute_query", lambda *a, **k: [{}, {}])
    identity = dict(
        product_code="P", supplier_code="F", supplier_store="01",
        manufacturer_code="M", manufacturer_store="01",
        grade_reference="", branch="01",
    )
    with pytest.raises(RuntimeError, match="Anomalia de identidade"):
        repo.get_supplier_link(**identity)


def test_get_supplier_link_uses_full_seven_field_identity():
    import inspect
    from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import (
        ProductSuppliersRepository,
    )

    source = inspect.getsource(ProductSuppliersRepository.get_supplier_link)
    for field in ("A5_FILIAL", "A5_FORNECE", "A5_LOJA", "A5_PRODUTO",
                  "A5_FABR", "A5_FALOJA", "A5_REFGRD"):
        assert field in source
