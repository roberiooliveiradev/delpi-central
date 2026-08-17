"""Regressão: coluna/tabela ausente no plugins DB → PluginsSchemaOutdatedError."""

from __future__ import annotations

from psycopg.errors import UndefinedColumn, UndefinedTable

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
    PluginsSchemaOutdatedError,
    wrap_plugins_db_error,
)


def test_wrap_undefined_column_is_schema_outdated() -> None:
    err = wrap_plugins_db_error(
        "fetch_all",
        UndefinedColumn("column \"public_booking_enabled\" does not exist"),
    )
    assert isinstance(err, PluginsSchemaOutdatedError)
    assert "desatualizado" in str(err).lower()
    assert "run_plugins_migrations" in str(err)


def test_wrap_undefined_table_is_schema_outdated() -> None:
    err = wrap_plugins_db_error(
        "fetch_all",
        UndefinedTable('relation "scheduling.resources" does not exist'),
    )
    assert isinstance(err, PluginsSchemaOutdatedError)


def test_wrap_other_errors_stay_generic() -> None:
    err = wrap_plugins_db_error("fetch_all", RuntimeError("boom"))
    assert type(err) is PluginsRepositoryError
    assert "fetch_all" in str(err)
    assert not isinstance(err, PluginsSchemaOutdatedError)
